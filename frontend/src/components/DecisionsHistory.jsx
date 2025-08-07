import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Alert,
  CircularProgress,
  Collapse,
  IconButton
} from '@mui/material';
import { ExpandMore, ExpandLess } from '@mui/icons-material';

const DecisionsHistory = ({ user }) => {
  const [decisions, setDecisions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [expandedRows, setExpandedRows] = useState({});

  useEffect(() => {
    if (user) {
      fetchDecisions();
    }
  }, [user]);

  const fetchDecisions = async () => {
    try {
      setLoading(true);
      setError('');
      
      const response = await fetch('http://localhost:8000/api/v1/decisions/', {
        method: 'GET',
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        setDecisions(data.decisions || []);
      } else {
        setError('Kararlar yüklenirken hata oluştu');
      }
    } catch (err) {
      setError('Ağ hatası oluştu');
      console.error('Decisions fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleRowExpansion = (decisionId) => {
    setExpandedRows(prev => ({
      ...prev,
      [decisionId]: !prev[decisionId]
    }));
  };

  const getDecisionColor = (decision) => {
    switch (decision) {
      case 'APPROVED':
        return 'success';
      case 'REJECTED':
        return 'error';
      case 'MANUAL_REVIEW':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getDecisionText = (decision) => {
    switch (decision) {
      case 'APPROVED':
        return 'Onaylandı';
      case 'REJECTED':
        return 'Reddedildi';
      case 'MANUAL_REVIEW':
        return 'Manuel İnceleme';
      default:
        return decision;
    }
  };

  const getDocumentTypeText = (docType) => {
    switch (docType) {
      case 'eft_form':
        return 'EFT Formu';
      case 'loan_application':
        return 'Kredi Başvurusu';
      case 'account_opening':
        return 'Hesap Açma';
      case 'complaint':
        return 'Şikayet';
      default:
        return 'Diğer';
    }
  };

  if (!user) {
    return null;
  }

  return (
    <Card sx={{ mt: 3 }}>
      <CardContent>
        <Typography variant="h6" gutterBottom sx={{ color: '#2e7d32', fontWeight: 'bold' }}>
          Geçmiş Kararlar
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {loading ? (
          <Box display="flex" justifyContent="center" p={3}>
            <CircularProgress />
          </Box>
        ) : decisions.length === 0 ? (
          <Alert severity="info">
            Henüz hiç belge işleme kararınız bulunmuyor.
          </Alert>
        ) : (
          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow sx={{ backgroundColor: '#f5f5f5' }}>
                  <TableCell />
                  <TableCell><strong>Müşteri Adı</strong></TableCell>
                  <TableCell><strong>TCKN</strong></TableCell>
                  <TableCell><strong>Belge Tipi</strong></TableCell>
                  <TableCell><strong>Niyet</strong></TableCell>
                  <TableCell><strong>Karar</strong></TableCell>
                  <TableCell><strong>Tarih</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {decisions.map((decision) => (
                  <React.Fragment key={decision.id}>
                    <TableRow hover>
                      <TableCell>
                        <IconButton
                          size="small"
                          onClick={() => toggleRowExpansion(decision.id)}
                        >
                          {expandedRows[decision.id] ? <ExpandLess /> : <ExpandMore />}
                        </IconButton>
                      </TableCell>
                      <TableCell>{decision.customer_name || 'Belirtilmemiş'}</TableCell>
                      <TableCell>{decision.customer_tckn || 'Belirtilmemiş'}</TableCell>
                      <TableCell>{getDocumentTypeText(decision.document_type)}</TableCell>
                      <TableCell>{decision.intent || 'Belirtilmemiş'}</TableCell>
                      <TableCell>
                        <Chip
                          label={getDecisionText(decision.decision)}
                          color={getDecisionColor(decision.decision)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        {new Date(decision.created_at).toLocaleDateString('tr-TR')}
                      </TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell colSpan={7} sx={{ py: 0 }}>
                        <Collapse in={expandedRows[decision.id]} timeout="auto" unmountOnExit>
                          <Box sx={{ p: 2, backgroundColor: '#fafafa' }}>
                            <Typography variant="subtitle2" gutterBottom>
                              <strong>Detaylar:</strong>
                            </Typography>
                            <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
                              <Box>
                                <Typography variant="body2">
                                  <strong>Belge ID:</strong> {decision.document_id}
                                </Typography>
                                <Typography variant="body2">
                                  <strong>İşlem Tutarı:</strong> {decision.transaction_amount ? `${decision.transaction_amount.toLocaleString('tr-TR')} ${decision.transaction_currency || 'TL'}` : 'Belirtilmemiş'}
                                </Typography>
                              </Box>
                              <Box>
                                <Typography variant="body2">
                                  <strong>İşlem Süresi:</strong> {decision.processing_time ? `${decision.processing_time}s` : 'Belirtilmemiş'}
                                </Typography>
                              </Box>
                            </Box>
                            
                            {decision.risk_factors && Array.isArray(decision.risk_factors) && decision.risk_factors.length > 0 && (
                              <Box sx={{ mt: 2 }}>
                                <Typography variant="body2" gutterBottom>
                                  <strong>Risk Faktörleri:</strong>
                                </Typography>
                                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                                  {decision.risk_factors.map((factor, index) => (
                                    <Chip
                                      key={index}
                                      label={factor}
                                      size="small"
                                      color="warning"
                                      variant="outlined"
                                    />
                                  ))}
                                </Box>
                              </Box>
                            )}

                            {decision.risk_factors && !Array.isArray(decision.risk_factors) && (
                              <Box sx={{ mt: 2 }}>
                                <Typography variant="body2" gutterBottom>
                                  <strong>Risk Faktörleri:</strong>
                                </Typography>
                                <Typography variant="body2">{decision.risk_factors}</Typography>
                              </Box>
                            )}

                            {decision.decision_reasons && Array.isArray(decision.decision_reasons) && decision.decision_reasons.length > 0 && (
                              <Box sx={{ mt: 2 }}>
                                <Typography variant="body2" gutterBottom>
                                  <strong>Karar Nedenleri:</strong>
                                </Typography>
                                <ul style={{ margin: 0, paddingLeft: 20 }}>
                                  {decision.decision_reasons.map((reason, index) => (
                                    <li key={index}>
                                      <Typography variant="body2">{reason}</Typography>
                                    </li>
                                  ))}
                                </ul>
                              </Box>
                            )}

                            {decision.decision_reasons && !Array.isArray(decision.decision_reasons) && (
                              <Box sx={{ mt: 2 }}>
                                <Typography variant="body2" gutterBottom>
                                  <strong>Karar Nedenleri:</strong>
                                </Typography>
                                <Typography variant="body2">{decision.decision_reasons}</Typography>
                              </Box>
                            )}
                          </Box>
                        </Collapse>
                      </TableCell>
                    </TableRow>
                  </React.Fragment>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </CardContent>
    </Card>
  );
};

export default DecisionsHistory; 