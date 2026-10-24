# Turnaround Black Box

[English](#english) · [Türkçe](#türkçe)

## English

**Which ground operation should be improved to make aircraft ready earlier?**

A small operations research lab that models task dependencies, shared ground crews and counterfactual interventions across three synthetic aircraft. It distinguishes a long task from a task that actually controls readiness.

### Run locally

Python 3.11+; no third-party dependencies, API keys or accounts.

```bash
python3 -m turnaround
```

Open **http://127.0.0.1:8001**. Another port: `python3 -m turnaround --port 8010`.

1. Choose an operation and add 0–60 minutes to its processing duration.
2. Set a hypothetical reduction budget of 0–20 minutes for one task.
3. Compare the disrupted schedule, best tested intervention and flight-priority scenario.
4. Hover over operations to inspect timing, shared resources and binding predecessors.
5. Expand the uncertainty experiment to inspect P50/P90 readiness times and simulated on-time proportions.

### Model

Three aircraft arrive at 09:00, 09:12 and 09:24, with readiness targets 55 minutes after arrival. Each has six tasks: unloading, cleaning, fuel, catering, loading and boarding. There is one shared baggage team and one shared cleaning team; other resources are dedicated to each aircraft.

Loading follows unloading. Boarding follows cleaning, catering and fuel under the **illustrative policy selected for this model**; this is not a universal airline procedure. All six tasks must finish before readiness.

```text
start(task) = max(arrival, completion of dependencies, resource availability)
ready(flight) = max(completion of its tasks)
delay(flight) = max(0, ready − target)
objective = sum(delay across flights)
```

A nonpreemptive serial schedule generator chooses the eligible task with earliest feasible start, then flight priority, then task ID. Resources have capacity one. Priority only breaks equal-start ties; it does not reserve a team or guarantee an earlier result. This is a deterministic heuristic, not a global optimization solver.

The highlighted chain traces all binding task and resource predecessors backwards from each aircraft's last task. It describes the generated schedule, including cross-aircraft crew waits; it is not proof that every highlighted task has positive marginal benefit.

### Counterfactuals and interventions

The selected disruption extends processing duration, rather than introducing a separate release delay. The engine reruns the scheduler after reducing each candidate task by the budget (clamped to a minimum one-minute duration). It ranks candidates by total readiness-delay minutes saved. Benefits are measured individually and cannot be added. A resource-order change can produce a negative benefit under the heuristic. If none improves the schedule, retain the baseline.

The disruption effect compares the disrupted schedule with the same model without the added duration. It is a model-based counterfactual, not causal evidence from real operations. The intervention budget represents hypothetical time savings, not a costed staffing or safety recommendation.

### Uncertainty experiment

200 reproducible runs, random seed 42, on the **undisrupted** scenario. Each task independently samples a triangular multiplier with minimum 0.8, mode 1.0 and maximum 1.4. Durations are rounded and clamped to one minute. P50/P90 use sorted-sample indices `floor(p × (n−1))`. These distributions are assumptions, not estimates calibrated on airline data.

### Structure and API

- `turnaround/engine.py`: scheduling, binding chains, interventions and uncertainty.
- `turnaround/__main__.py`: loopback-only standard-library HTTP server.
- `turnaround/index.html`: responsive dashboard without external assets.
- `tests/test_engine.py`: hand-calculated checks, independent physical constraints and reproducibility.

`GET /api/scenario?task=TB101-clean&extra=15&saving=8&priority=TB101`

`GET /api/uncertainty`

Invalid scenario parameters return HTTP 400. Unknown routes return 404.

```bash
python3 -m unittest discover -s tests -v
python3 -c 'from turnaround.engine import scenario; s=scenario(); print(s["selected"])'
```

GitHub Actions tests Python 3.11–3.13. The constraints test checks 54 task/disruption combinations across baseline, intervention and priority schedules.

### Limitations and next steps

Synthetic aircraft, routes, durations and procedures; no airline affiliation. Readiness is **not takeoff**: ATC, taxi, runway availability, crew legality, maintenance, passenger connections, operational approvals and real safety procedures are excluded. No predictive AI model or real-world performance claim. The HTTP server is for local development.

Next experiments: compare the heuristic with an exact CP-SAT model; introduce staffing costs and multiple teams; calibrate duration distributions on appropriately licensed observations; add correlated service disruptions and explicit release delays.

## Türkçe

**Uçağı daha erken hazır hale getirmek için hangi yer hizmetine müdahale edilmeli?**

Bu proje, üç sentetik uçak için işlem bağımlılıklarını ve ortak yer hizmetleri ekiplerini modelleyen bir yöneylem araştırması uygulamasıdır. Uzun süren işlem ile hazır olma zamanını gerçekten belirleyen işlemi birbirinden ayırır.

### Çalıştırma ve kullanım

Python 3.11 veya üzeri yeterlidir. Ek paket, API anahtarı veya hesap gerekmez.

```bash
python3 -m turnaround
```

Tarayıcıda **http://127.0.0.1:8001** adresini açın. Port doluysa `python3 -m turnaround --port 8010` kullanın.

1. Bir işlem seçip süresine 0–60 dakika ekleyin.
2. Tek bir işlemden kazanılabilecek varsayımsal süreyi 0–20 dakika arasında seçin.
3. Aksaklık planını, en iyi denenmiş müdahaleyi ve uçuş önceliği senaryosunu karşılaştırın.
4. Zaman çizelgesindeki işlemlerin üzerine gelerek zamanları, kaynakları ve beklemeye neden olan öncülleri inceleyin.
5. Belirsizlik bölümünde 200 simülasyonun ortanca ve yüzde 90 hazır olma zamanlarını, hedefe yetişme oranlarını görün.

### Modelin çalışma biçimi

Üç uçak 09:00, 09:12 ve 09:24'te gelir; hedefleri varıştan 55 dakika sonra hazır olmaktır. Her uçakta bagaj boşaltma, temizlik, yakıt, ikram, bagaj yükleme ve yolcu alımı bulunur. Bir bagaj ekibi ve bir temizlik ekibi paylaşılır; diğer hizmet kaynakları uçağa özeldir.

Bagaj yükleme boşaltmadan sonra; yolcu alımı ise temizlik, ikram ve yakıt tamamlandıktan sonra başlar. Bu sıralama **bu örnek için seçilmiş bir varsayımdır**, bütün havayollarının prosedürü değildir. Hazır olma için altı işlemin tamamlanması gerekir.

```text
başlangıç = max(varış, bağımlı işlemlerin bitişi, ekibin müsaitliği)
hazır olma = uçağın işlemlerinin en geç bitişi
gecikme = max(0, hazır olma − hedef)
amaç = tüm uçakların hazır olma gecikmeleri toplamı
```

Algoritma, başlayabilir işlemler arasından en erken uygun başlangıca sahip olanı seçer. Eşitlikte uçuş önceliği, sonra işlem kimliği kullanılır. İşler bölünmez; ekipler aynı anda tek iş yapar. Öncelik yalnızca eşit başlangıçlarda etkilidir; ekip rezervasyonu veya iyileşme garantisi değildir. Yöntem sezgiseldir, küresel optimum iddiası yoktur.

Turuncu zincir, her uçağın son işleminden geriye doğru bağlayıcı işlem ve kaynak beklemelerini izler. Başka bir uçaktaki ekip işi de zincire girebilir. Turuncu gösterilen her işi hızlandırmanın mutlaka fayda sağlayacağı anlamına gelmez.

### Müdahale ve karşılaştırmalar

Eklenen aksaklık, işlemin çalışma süresini uzatır; ayrı bir işe başlayabilme gecikmesi değildir. Her aday işlem seçilen bütçe kadar kısaltılır ve bütün plan tekrar hesaplanır. İşlemler en az bir dakika sürer. Seçenekler, toplam hazır olma gecikmesinde sağladıkları kazanca göre sıralanır. Ayrı müdahalelerin kazançları toplanamaz. Sezgisel algoritmada ekip sırası değişirse olumsuz sonuç da çıkabilir; iyileştirme yoksa mevcut plan korunmalıdır.

Aksaklığın etkisi, aynı planın ek süre verilmemiş haliyle karşılaştırılır. Bu, modele dayalı bir karşılaştırmadır; gerçek veriden çıkarılmış nedensellik kanıtı değildir. Süre kazanımı bütçesi, maliyetlendirilmiş bir personel veya emniyet önerisi değildir.

### Belirsizlik deneyi

Aksaklık eklenmemiş senaryo için, 42 sabit rastgelelik tohumu ile 200 tekrar yapılır. İşlem süreleri birbirinden bağımsız olarak en az 0,8; en olası 1,0; en fazla 1,4 çarpanlı üçgensel dağılımla örneklenir. Süreler yuvarlanır ve en az bir dakika olur. P50/P90, sıralanmış örneklerde `floor(p × (n−1))` indisinden alınır. Bu dağılımlar havayolu verileriyle doğrulanmış tahminler değil, deney varsayımlarıdır.

### Dosyalar, testler ve API

`turnaround/engine.py` hesaplama motorunu, `turnaround/__main__.py` yerel HTTP sunucusunu, `turnaround/index.html` görsel paneli içerir. Panel dili İngilizcedir; bu belge iki dillidir.

```bash
python3 -m unittest discover -s tests -v
```

Testler; elle hesaplanan ekip beklemesini, işlem bağımlılıklarını, kaynak çakışmalarını, müdahalelerin tekrar hesaplanmasını, geçersiz girdileri ve aynı tohumla tekrarlanabilirliği kontrol eder. 54 farklı aksaklık durumu, üç plan türünde fiziksel kısıtlar açısından denetlenir. GitHub Actions, Python 3.11–3.13 için yapılandırılmıştır.

Senaryo API'si: `GET /api/scenario?task=TB101-clean&extra=15&saving=8&priority=TB101`. Belirsizlik API'si: `GET /api/uncertainty`. Geçersiz senaryo girdileri HTTP 400, bilinmeyen adresler 404 döndürür.

### Sınırlar ve geliştirme fikirleri

Uçaklar, rotalar, süreler ve prosedürler sentetiktir. Proje herhangi bir havayoluna bağlı değildir. Hazır olmak, havalanmak anlamına gelmez: ATC, taksi, pist, mürettebat çalışma kuralları, bakım, yolcu bağlantıları ve gerçek operasyon emniyet prosedürleri kapsam dışındadır. Tahmin yapan bir yapay zekâ modeli veya gerçek operasyon başarısı iddiası bulunmaz. Sunucu yerel geliştirme içindir.

Sonraki çalışmalar: CP-SAT ile kesin çözüm karşılaştırması, ekip maliyetleri ve çoklu ekipler, uygun lisanslı verilerle süre dağılımlarını kalibre etme, ilişkili aksaklıklar ve ayrı işe başlama gecikmeleri.
