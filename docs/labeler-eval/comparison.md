# Labeler Comparison

Generated: 2026-04-30 12:02:46 UTC

Inputs:
- `labeler-eval-gemini.json` — provider `gemini`, 0/5 ok, $0.0000 total
- `labeler-eval-claude-opus-chat.json` — provider `claude-opus-4-7-chat`, 10/10 ok, $0.0000 total

## Headline stats

| provider | ok/total | entities found | cost_usd |
|---|---|---|---|
| gemini | 0/5 | 0 | $0.0000 |
| claude-opus-4-7-chat | 10/10 | 52 | $0.0000 |

## Entity counts (per provider)

| entity | gemini | claude-opus-4-7-chat |
|---|---|---|
| DATASET | 0 | 7 |
| DERGİ | 0 | 2 |
| KURUM | 0 | 6 |
| METODOLOJI | 0 | 13 |
| METRİK | 0 | 10 |
| YAZAR | 0 | 8 |
| YIL | 0 | 6 |

## Per-paragraph entities

### sp-001

> Yılmaz, A.M. (2023). Boğaziçi Üniversitesi'nde yapılan çalışmada BERT modeli IMDB veri seti üzerinde F1 skoru ile değerlendirildi.

**gemini**: FAILED — ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'Your prepayment credits are depleted. Please go

**claude-opus-4-7-chat** (6 entities):
- `YAZAR` "Yılmaz, A.M." (0-12)
- `YIL` "2023" (14-18)
- `KURUM` "Boğaziçi Üniversitesi" (21-42)
- `METODOLOJI` "BERT" (65-69)
- `DATASET` "IMDB" (77-81)
- `METRİK` "F1 skoru" (101-109)

### sp-002

> Bu tez çalışmasında, derin öğrenme yöntemlerinden CNN ve LSTM modelleri kullanılarak Türkçe duygu analizi gerçekleştirilmiştir. ODTÜ Bilgisayar Mühendisliği bölümünde 2024 yılında yapılan deneyler, ROUGE-L değeri 0.42 olarak ölçülmüştür.

**gemini**: FAILED — ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'Your prepayment credits are depleted. Please go

**claude-opus-4-7-chat** (5 entities):
- `METODOLOJI` "CNN" (50-53)
- `METODOLOJI` "LSTM" (57-61)
- `KURUM` "ODTÜ Bilgisayar Mühendisliği" (128-156)
- `YIL` "2024" (167-171)
- `METRİK` "ROUGE-L" (198-205)

### sp-003

> Demir, K., & Kaya, S. (2022). Sağlık alanında doğal dil işleme uygulamaları. Türk Bilişim Dergisi, 15(3), 45-67. Çalışmada Random Forest ve XGBoost modelleri Hacettepe Üniversitesi Tıp Fakültesi veri seti üzerinde karşılaştırılmıştır.

**gemini**: FAILED — ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'Your prepayment credits are depleted. Please go

**claude-opus-4-7-chat** (7 entities):
- `YAZAR` "Demir, K." (0-9)
- `YAZAR` "Kaya, S." (13-21)
- `YIL` "2022" (23-27)
- `DERGİ` "Türk Bilişim Dergisi" (77-97)
- `METODOLOJI` "Random Forest" (123-136)
- `METODOLOJI` "XGBoost" (140-147)
- `KURUM` "Hacettepe Üniversitesi Tıp Fakültesi" (158-194)

### sp-004

> Sosyal medya analizi için Twitter veri seti üzerinde Naive Bayes sınıflandırıcısı uygulanmış, doğruluk %78 olarak elde edilmiştir.

**gemini**: FAILED — ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'Your prepayment credits are depleted. Please go

**claude-opus-4-7-chat** (3 entities):
- `DATASET` "Twitter veri seti" (26-43)
- `METODOLOJI` "Naive Bayes" (53-64)
- `METRİK` "doğruluk" (94-102)

### sp-005

> Çetin, A. (2021). Türkçe akademik metinlerde ders konusu çıkarımı. Yıldız Teknik Üniversitesi, Doktora Tezi. Gradient Boosting algoritması ile WikiNeural veri seti üzerinde Precision %92 oranında elde edilmiştir.

**gemini**: FAILED — ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'Your prepayment credits are depleted. Please go

**claude-opus-4-7-chat** (6 entities):
- `YAZAR` "Çetin, A." (0-9)
- `YIL` "2021" (11-15)
- `KURUM` "Yıldız Teknik Üniversitesi" (67-93)
- `METODOLOJI` "Gradient Boosting" (109-126)
- `DATASET` "WikiNeural" (143-153)
- `METRİK` "Precision" (173-182)

### sp-006

> Bu makalede, mT5 tabanlı Türkçe akademik özetleme modeli önerilmiştir. Marmara Üniversitesi tez koleksiyonundan alınan 5000 makale ile Spearman korelasyonu 0.85 olarak hesaplanmıştır.

**gemini**: (no data)

**claude-opus-4-7-chat** (3 entities):
- `METODOLOJI` "mT5" (13-16)
- `KURUM` "Marmara Üniversitesi" (71-91)
- `METRİK` "Spearman" (135-143)

### sp-007

> Karadeniz, M. (2020). Görüntü işleme alanında ResNet-50 mimarisi ile CIFAR-10 veri seti üzerinde mAP değeri 0.81 elde edilmiştir. KTÜ Elektrik-Elektronik Mühendisliği'nde yapılan çalışma.

**gemini**: (no data)

**claude-opus-4-7-chat** (6 entities):
- `YAZAR` "Karadeniz, M." (0-13)
- `YIL` "2020" (15-19)
- `METODOLOJI` "ResNet-50" (46-55)
- `DATASET` "CIFAR-10" (69-77)
- `METRİK` "mAP" (97-100)
- `KURUM` "KTÜ Elektrik-Elektronik Mühendisliği" (130-166)

### sp-008

> Önerilen yöntem, Transformer mimarisi kullanılarak Mukayese benchmark'ında değerlendirilmiştir. METEOR skoru 0.34, BLEU değeri ise 0.28 olarak ölçülmüştür.

**gemini**: (no data)

**claude-opus-4-7-chat** (4 entities):
- `METODOLOJI` "Transformer" (17-28)
- `DATASET` "Mukayese" (51-59)
- `METRİK` "METEOR" (96-102)
- `METRİK` "BLEU" (115-119)

### sp-009

> Akın, B., Yıldız, R., & Şahin, T. (2025). Eğitim teknolojileri üzerine sistematik bir derleme. Anadolu Üniversitesi Eğitim Fakültesi Dergisi, 28(1). k-NN sınıflandırıcı PISA 2018 veri seti üzerinde test edilmiş, MSE 0.045 olarak raporlanmıştır.

**gemini**: (no data)

**claude-opus-4-7-chat** (8 entities):
- `YAZAR` "Akın, B." (0-8)
- `YAZAR` "Yıldız, R." (10-20)
- `YAZAR` "Şahin, T." (24-33)
- `YIL` "2025" (35-39)
- `DERGİ` "Anadolu Üniversitesi Eğitim Fakültesi Dergisi" (95-140)
- `METODOLOJI` "k-NN" (149-153)
- `DATASET` "PISA 2018" (169-178)
- `METRİK` "MSE" (212-215)

### sp-010

> Bu çalışmada XLM-RoBERTa modeli, Türkçe NER görevinde WikiANN-tr veri seti üzerinde fine-tune edilmiştir. Cohen Kappa skoru 0.87 olarak elde edilmiş, BERTurk ile karşılaştırıldığında %3 iyileşme sağlanmıştır.

**gemini**: (no data)

**claude-opus-4-7-chat** (4 entities):
- `METODOLOJI` "XLM-RoBERTa" (13-24)
- `DATASET` "WikiANN-tr" (54-64)
- `METRİK` "Cohen Kappa" (106-117)
- `METODOLOJI` "BERTurk" (150-157)
