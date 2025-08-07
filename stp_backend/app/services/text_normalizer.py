import re
import logging
from typing import List

logger = logging.getLogger(__name__)

class TextNormalizer:
    def __init__(self):
        # Türkçe karakterler için özel karakterler
        self.tr_chars = {
            'İ': 'I', 'I': 'ı', 'Ş': 'S', 'Ğ': 'G', 'Ü': 'U', 'Ö': 'O', 'Ç': 'C',
            'i': 'i', 'ş': 's', 'ğ': 'g', 'ü': 'u', 'ö': 'o', 'ç': 'c', 'ı': 'i'
        }
        
        # Para birimleri için regex pattern
        self.currency_pattern = r'\d+\.?\s*\d*\s*,?\s*\d*\s*(?:TL|USD|EUR|₺|\$|€|TRY)'
        
        # IBAN için regex pattern (TR ile başlayan)
        self.iban_pattern = r'TR[0-9A-Z]{2}\s*[0-9]{4}\s*[0-9]{4}\s*[0-9]{4}\s*[0-9]{4}\s*[0-9]{4}\s*[0-9]{2}'
        
        # T.C. Kimlik No için pattern
        self.tckn_pattern = r'\b\d{11}\b'

    def fix_ocr_errors(self, text: str) -> str:
        """OCR hatalarını düzelt"""
        
        # IBAN düzeltmeleri (TR ile başlayan)
        def fix_iban_errors(match):
            iban = match.group()
            # IBAN'da sadece sayı-harf düzeltmeleri yap
            iban = iban.replace('O', '0').replace('o', '0')
            iban = iban.replace('I', '1').replace('l', '1')
            iban = iban.replace('S', '5').replace('B', '8')
            iban = iban.replace('G', '6').replace('E', '8')
            return iban

        # IBAN'ları düzelt
        text = re.sub(self.iban_pattern, fix_iban_errors, text)
        
        # Hesap numaralarını düzelt (15-25 haneli sayılar)
        def fix_account_numbers(match):
            number = match.group()
            number = number.replace('O', '0').replace('o', '0')
            number = number.replace('I', '1').replace('l', '1')
            number = number.replace('S', '5').replace('B', '8')
            number = number.replace('G', '6').replace('E', '8')
            return number
        
        # Hesap numaralarını bul ve düzelt (sadece sayı içeren uzun diziler)
        text = re.sub(r'\b[0-9OoIlSBGE\s]{15,25}\b', fix_account_numbers, text)
        
        # Tarih düzeltmeleri (O2 -> 02 gibi)
        text = re.sub(r'\bO(\d)\b', r'0\1', text)  # O2 -> 02
        
        return text

    def fix_company_names(self, text: str) -> str:
        """Şirket isimlerindeki yaygın hataları düzelt"""
        fixes = {
            'AJŞ': 'A.Ş.',
            'AŞ': 'A.Ş.',
            'LTD': 'Ltd.',
            'ŞTİ': 'Şti.',
            'STI': 'Şti.',
            'ŞTI': 'Şti.',
            'LİMİTED': 'Limited',
            'KOLLEKTIF': 'Koll.',
            'KOMANDIT': 'Kom.',
            'ANONIM': 'Anonim',
        }
        
        for wrong, correct in fixes.items():
            # Kelime sınırlarında eşleşme
            text = re.sub(r'\b' + re.escape(wrong) + r'\b', correct, text, flags=re.IGNORECASE)
        
        return text

    def fix_banking_terms(self, text: str) -> str:
        """Bankacılık terimlerindeki hataları düzelt"""
        fixes = {
            'IBAN nolu': 'IBAN numaralı',
            'nolu hesab': 'numaralı hesab',
            'nezdinde': 'nezdinde',
            'tutarını': 'tutarını',
            'aktarmak': 'aktarmak',
            'talep ederiz': 'talep ederiz',
            'Gereğinin': 'Gereğinin',
            'yapılmasını': 'yapılmasını',
        }
        
        for wrong, correct in fixes.items():
            text = re.sub(re.escape(wrong), correct, text, flags=re.IGNORECASE)
        
        return text

    def normalize_whitespace(self, text: str) -> str:
        """Boşlukları normalize et"""
        # Birden fazla boşluğu tek boşluğa indir
        text = re.sub(r'\s+', ' ', text)
        # Satır sonlarını düzelt
        text = re.sub(r'\n+', '\n', text)
        return text.strip()

    def normalize_punctuation(self, text: str) -> str:
        """Noktalama işaretlerini normalize et"""
        # Gereksiz noktalama işaretlerini kaldır
        text = re.sub(r'[^\w\s.,;:!?(){}[\]"\'₺$€/\-]', '', text)
        
        # Çoklu noktaları düzelt (. . . -> .)
        text = re.sub(r'\.(\s*\.)+', '.', text)
        
        # Nokta + boşluk + nokta dizilerini düzelt
        text = re.sub(r'\.\s+\.', '.', text)
        
        # Şirket isimlerindeki fazla noktaları düzelt
        text = re.sub(r'(A\.\s*Ş\.\s*\.)', 'A.Ş.', text)
        text = re.sub(r'(Ltd\.\s*\.\s*Şti\.\s*\.)', 'Ltd. Şti.', text)
        text = re.sub(r'(Ltd\.\s*\.)', 'Ltd.', text)
        text = re.sub(r'(Şti\.\s*\.)', 'Şti.', text)
        
        # Noktalama işaretlerinden sonra boşluk ekle (sadece gerekli yerlerde)
        text = re.sub(r'([.,;:!?()])\s*', r'\1 ', text)
        
        return text

    def normalize_currency(self, text: str) -> str:
        """Para birimlerini normalize et"""
        # TRY ile TL arasında tutarlılık sağla
        text = re.sub(r'\bTRY\b', 'TL', text)
        
        # Para miktarlarındaki gereksiz boşlukları ve noktaları temizle
        # Örnekler: "100. 000, 00" -> "100.000,00"
        def fix_currency_amount(match):
            amount = match.group()
            
            # İlk önce para birimini ayır
            currency_match = re.search(r'(TL|USD|EUR|₺|\$|€)$', amount)
            currency = currency_match.group() if currency_match else 'TL'
            number_part = amount.replace(currency, '').strip()
            
            # Sayı kısmındaki boşlukları kaldır
            number_part = re.sub(r'\s+', '', number_part)
            
            # Nokta ve virgül düzeltmeleri
            # 100.000,00 formatını koru, 100. 000, 00 gibi bozuk formatları düzelt
            if ',' in number_part and '.' in number_part:
                # Binlik ayracı nokta, ondalık ayracı virgül
                parts = number_part.split(',')
                if len(parts) == 2:
                    integer_part = parts[0].replace('.', '')
                    decimal_part = parts[1]
                    # Binlik ayraçlarını ekle
                    if len(integer_part) > 3:
                        formatted_integer = f"{integer_part[:-3]}.{integer_part[-3:]}"
                    else:
                        formatted_integer = integer_part
                    number_part = f"{formatted_integer},{decimal_part}"
            
            return f"{number_part} {currency}"

        # Para tutarlarını bul ve düzelt
        text = re.sub(self.currency_pattern, fix_currency_amount, text)
        
        return text

    def normalize_iban(self, text: str) -> str:
        """IBAN numaralarını normalize et"""
        def format_iban(match):
            iban = match.group()
            # Tüm boşlukları kaldır
            iban = re.sub(r'\s+', '', iban)
            # 4'er gruplar halinde formatla
            formatted = ' '.join([iban[i:i+4] for i in range(0, len(iban), 4)])
            return formatted

        return re.sub(self.iban_pattern, format_iban, text)

    def normalize_tckn(self, text: str) -> str:
        """T.C. Kimlik numaralarını normalize et"""
        return re.sub(self.tckn_pattern, lambda x: x.group().strip(), text)

    def fix_turkish_chars(self, text: str) -> str:
        """OCR'dan yanlış tanınan Türkçe karakterleri düzelt"""
        # Yaygın OCR hatalarını düzelt
        replacements = {
            'l.': 'İ',  # OCR genelde İ harfini l. olarak tanıyor
            '|': 'I',   # | karakteri genelde I olarak kullanılıyor
            '¢': 'ç',   # ç harfi bazen ¢ olarak tanınıyor
            '§': 'ş',   # ş harfi bazen § olarak tanınıyor
            'ü': 'ü',   # ü karakteri
            'ğ': 'ğ',   # ğ karakteri
            'ı': 'ı',   # ı karakteri
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
            
        return text

    def normalize(self, text: str) -> str:
        """Tüm normalizasyon işlemlerini uygula"""
        if not text:
            return text

        logger.info("Metin normalizasyonu başlıyor...")
        
        # Normalizasyon adımları (sırası önemli)
        text = self.fix_turkish_chars(text)
        text = self.fix_ocr_errors(text)  # OCR hatalarını düzelt
        text = self.normalize_whitespace(text)  # Boşlukları önce düzelt
        text = self.fix_company_names(text)  # Şirket isimlerini düzelt
        text = self.fix_banking_terms(text)  # Bankacılık terimlerini düzelt
        text = self.normalize_punctuation(text)  # Noktalama işaretlerini düzelt
        text = self.normalize_currency(text)  # Para birimlerini düzelt
        text = self.normalize_iban(text)  # IBAN'ları düzelt
        text = self.normalize_tckn(text)  # TCKN'leri düzelt
        text = self.normalize_whitespace(text)  # Son olarak tekrar boşlukları düzelt
        
        logger.info("Metin normalizasyonu tamamlandı")
        return text

text_normalizer = TextNormalizer() 