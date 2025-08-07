import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import pdf2image
import logging
import io
import numpy as np
from typing import List, Tuple, Optional
from .text_normalizer import text_normalizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OCRService:
    def __init__(self):
        # Tesseract konfigürasyonu - Türkçe ve İngilizce dil desteği
        self.tesseract_config = {
            # OCR Engine Mode: 3 = Default, based on what is available
            'oem': 3,
            # Page Segmentation Mode: 6 = Uniform block of text
            'psm': 6,
            # Dil desteği - Türkçe ve İngilizce
            'lang': 'tur+eng',
            # Whitelist karakterleri - Türkçe karakterler dahil
            'whitelist': 'ABCÇDEFGĞHIİJKLMNOÖPQRSŞTUÜVWXYZabcçdefgğhıijklmnoöpqrsştuüvwxyz0123456789.,;:!?()-/\\ ₺$€',
        }
        
        # DPI optimizasyon ayarları
        self.target_dpi = 300  # OCR için optimal DPI
        self.min_dpi = 150     # Minimum kabul edilebilir DPI
        self.max_dpi = 600     # Maximum DPI (performans için)

    def get_tesseract_config_string(self, custom_psm: Optional[int] = None) -> str:
        """Tesseract konfigürasyonunu string formatında döndür"""
        config = self.tesseract_config.copy()
        if custom_psm:
            config['psm'] = custom_psm
            
        config_string = f"--oem {config['oem']} --psm {config['psm']} -c tessedit_char_whitelist={config['whitelist']}"
        return config_string

    def enhance_image_quality(self, image: Image.Image) -> Image.Image:
        """Görüntü kalitesini OCR için optimize et"""
        try:
            logger.info("Görüntü kalitesi optimize ediliyor...")
            
            # RGB formatına çevir
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # DPI kontrolü ve optimizasyonu
            image = self.optimize_dpi(image)
            
            # Gri tonlamaya çevir (OCR için daha iyi)
            image = image.convert('L')
            
            # Kontrast artırma
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)  # %50 kontrast artışı
            
            # Keskinlik artırma
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(2.0)  # %100 keskinlik artışı
            
            # Gürültü azaltma filtresi
            image = image.filter(ImageFilter.MedianFilter(size=3))
            
            # Threshold uygulama (siyah-beyaz yapma)
            image = self.apply_threshold(image)
            
            logger.info("Görüntü kalitesi optimizasyonu tamamlandı")
            return image
            
        except Exception as e:
            logger.error(f"Görüntü kalitesi optimizasyonu hatası: {e}")
            return image

    def optimize_dpi(self, image: Image.Image) -> Image.Image:
        """DPI optimizasyonu yaparak görüntüyü OCR için hazırla"""
        try:
            # Mevcut DPI bilgisini al
            current_dpi = image.info.get('dpi', (72, 72))
            if isinstance(current_dpi, tuple):
                current_dpi = current_dpi[0]
            elif isinstance(current_dpi, (list, tuple)) and len(current_dpi) > 0:
                current_dpi = current_dpi[0]
            else:
                current_dpi = 72  # Varsayılan DPI
                
            logger.info(f"Mevcut DPI: {current_dpi}")
            
            # DPI çok düşükse yeniden boyutlandır
            if current_dpi < self.min_dpi:
                scale_factor = self.target_dpi / current_dpi
                new_size = (int(image.width * scale_factor), int(image.height * scale_factor))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
                logger.info(f"Görüntü {scale_factor:.2f}x büyütüldü, yeni boyut: {new_size}")
                
            # DPI çok yüksekse küçült (performans için)
            elif current_dpi > self.max_dpi:
                scale_factor = self.target_dpi / current_dpi
                new_size = (int(image.width * scale_factor), int(image.height * scale_factor))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
                logger.info(f"Görüntü {scale_factor:.2f}x küçültüldü, yeni boyut: {new_size}")
            
            # DPI bilgisini güncelle
            image.info['dpi'] = (self.target_dpi, self.target_dpi)
            
            return image
            
        except Exception as e:
            logger.error(f"DPI optimizasyonu hatası: {e}")
            return image

    def apply_threshold(self, image: Image.Image) -> Image.Image:
        """Adaptive threshold uygulayarak siyah-beyaz yapma"""
        try:
            # PIL Image'ı numpy array'e çevir
            img_array = np.array(image)
            
            # Otsu's threshold yöntemi için basit implementasyon
            # Histogram hesapla
            histogram = np.histogram(img_array, bins=256, range=(0, 256))[0]
            
            # Optimal threshold değerini bul (Otsu yöntemi)
            total_pixels = img_array.size
            sum_total = sum(i * histogram[i] for i in range(256))
            
            sum_background = 0
            weight_background = 0
            max_variance = 0
            optimal_threshold = 0
            
            for i in range(256):
                weight_background += histogram[i]
                if weight_background == 0:
                    continue
                    
                weight_foreground = total_pixels - weight_background
                if weight_foreground == 0:
                    break
                    
                sum_background += i * histogram[i]
                mean_background = sum_background / weight_background
                mean_foreground = (sum_total - sum_background) / weight_foreground
                
                variance = weight_background * weight_foreground * (mean_background - mean_foreground) ** 2
                
                if variance > max_variance:
                    max_variance = variance
                    optimal_threshold = i
            
            # Threshold uygula
            binary_array = (img_array > optimal_threshold) * 255
            
            # Numpy array'ı PIL Image'a geri çevir
            return Image.fromarray(binary_array.astype(np.uint8))
            
        except Exception as e:
            logger.error(f"Threshold uygulama hatası: {e}")
            # Hata durumunda basit threshold uygula
            return image.point(lambda x: 0 if x < 128 else 255, '1')

    def preprocess_for_different_content_types(self, image: Image.Image, content_type: str) -> List[Image.Image]:
        """İçerik tipine göre farklı ön işleme teknikleri uygula"""
        processed_images = []
        
        try:
            # Temel optimizasyon (her zaman)
            base_image = self.enhance_image_quality(image)
            processed_images.append(base_image)
            
            # Bankacılık belgelerine özel optimizasyonlar
            if any(term in content_type.lower() for term in ['banking', 'financial', 'document']):
                # PSM 6: Uniform block of text (varsayılan)
                processed_images.append(base_image)
                
                # PSM 8: Treat the image as a single word
                # Küçük metin blokları için
                processed_images.append(base_image)
                
                # PSM 13: Raw line. Treat the image as a single text line
                # Tek satır metinler için (IBAN, hesap no vs.)
                processed_images.append(base_image)
            
            return processed_images
            
        except Exception as e:
            logger.error(f"İçerik tipine göre ön işleme hatası: {e}")
            return [image]

    def extract_text_from_image(self, image: Image.Image, content_type: str = "document") -> str:
        """Görüntüden metin çıkarma - gelişmiş konfigürasyon ile"""
        try:
            logger.info("Görüntüden OCR ile metin çıkarılıyor...")
            
            # İçerik tipine göre farklı ön işlemeler yap
            processed_images = self.preprocess_for_different_content_types(image, content_type)
            
            best_text = ""
            best_confidence = 0
            
            # Farklı PSM modları ile deneme
            psm_modes = [6, 8, 13, 3]  # Farklı page segmentation modları
            
            for i, processed_image in enumerate(processed_images):
                psm = psm_modes[min(i, len(psm_modes) - 1)]
                
                try:
                    # Tesseract konfigürasyonu
                    config = self.get_tesseract_config_string(custom_psm=psm)
                    
                    # OCR gerçekleştir
                    text = pytesseract.image_to_string(
                        processed_image, 
                        lang=self.tesseract_config['lang'],
                        config=config
                    )
                    
                    # Güven skorunu al
                    data = pytesseract.image_to_data(
                        processed_image,
                        lang=self.tesseract_config['lang'],
                        config=config,
                        output_type=pytesseract.Output.DICT
                    )
                    
                    # Ortalama güven skorunu hesapla
                    confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                    avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                    
                    logger.info(f"PSM {psm} - Güven skoru: {avg_confidence:.2f}%")
                    
                    # En iyi sonucu seç
                    if avg_confidence > best_confidence and len(text.strip()) > 0:
                        best_confidence = avg_confidence
                        best_text = text
                        
                except Exception as e:
                    logger.warning(f"PSM {psm} ile OCR hatası: {e}")
                    continue
            
            # En iyi sonuç bulunamadıysa varsayılan yöntemi kullan
            if not best_text.strip():
                logger.info("Varsayılan OCR yöntemi kullanılıyor...")
                config = self.get_tesseract_config_string()
                best_text = pytesseract.image_to_string(
                    processed_images[0] if processed_images else image,
                    lang=self.tesseract_config['lang'],
                    config=config
                )
            
            logger.info(f"OCR tamamlandı. En iyi güven skoru: {best_confidence:.2f}%")
            
            # Metni normalize et
            normalized_text = text_normalizer.normalize(best_text)
            
            return normalized_text
            
        except Exception as e:
            logger.error(f"OCR hatası: {e}")
            return ""

    def extract_text_from_pdf(self, pdf_content: bytes) -> str:
        """PDF'den metin çıkarma - gelişmiş ayarlarla"""
        try:
            logger.info("PDF'den OCR ile metin çıkarılıyor...")
            
            # PDF'i yüksek çözünürlükte görüntüye çevir
            images = pdf2image.convert_from_bytes(
                pdf_content,
                dpi=self.target_dpi,  # Yüksek DPI
                fmt='PNG',
                thread_count=2,  # Performans için
                grayscale=False,  # Renkli olarak al, sonra optimize ederiz
                size=None,  # Orijinal boyut
                transparent=False
            )
            
            all_text = []
            
            for i, image in enumerate(images):
                logger.info(f"PDF sayfa {i+1}/{len(images)} işleniyor...")
                
                # Her sayfa için OCR yap
                page_text = self.extract_text_from_image(image, "banking_document")
                
                if page_text.strip():
                    all_text.append(f"--- Sayfa {i+1} ---")
                    all_text.append(page_text)
            
            combined_text = "\n\n".join(all_text)
            logger.info(f"PDF OCR tamamlandı. {len(images)} sayfa işlendi.")
            
            return combined_text
            
        except Exception as e:
            logger.error(f"PDF OCR hatası: {e}")
            return ""

    def get_ocr_confidence(self, image: Image.Image) -> float:
        """OCR güven skorunu hesapla"""
        try:
            config = self.get_tesseract_config_string()
            data = pytesseract.image_to_data(
                image,
                lang=self.tesseract_config['lang'],
                config=config,
                output_type=pytesseract.Output.DICT
            )
            
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            return sum(confidences) / len(confidences) if confidences else 0.0
            
        except Exception as e:
            logger.error(f"Güven skoru hesaplama hatası: {e}")
            return 0.0

ocr_service = OCRService() 