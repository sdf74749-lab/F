# Host Migration Protocol (2-4 Players)

## 1) Peer metadata heartbeat
كل 1 ثانية يرسل كل لاعب:
- RTT
- packet loss
- battery level
- frame stability
- join order
- last acknowledged event index

## 2) Leader candidate score
```text
score = (100 - RTT_ms_clamped)
      + (100 - packet_loss_percent * 2)
      + battery_level_percent
      + host_history_bonus
      + sync_freshness_bonus
```

أعلى score يصبح shadow host ثم host فعلي عند الطوارئ.

## 3) Snapshot strategy
- Snapshot كامل كل 5 أحداث.
- Event log incremental لكل رمية/حركة.
- كل Client يحتفظ بآخر snapshot + index + state hash.

## 4) Host leave flow
1. اكتشاف timeout (مثلاً 1500ms).
2. shadow host يعلن `HOST_TAKEOVER` مع snapshot hash وevent index.
3. باقي اللاعبين يرسلون ACK.
4. عند majority ACK يبدأ host الجديد بث الحالة.
5. إذا لم تتحقق majority خلال 2 ثانية => إعادة انتخاب سريعة.

## 5) Rejoin
- اللاعب المنفصل يستطيع الرجوع خلال نافذة 20 ثانية.
- يحصل على snapshot + delta events فقط.
- في حال divergence يتم forced-resync.

## 6) Security
- Session key per match.
- كل message يحمل nonce + monotonic counter ضد replay.
- catalog/data-at-rest: stream cipher + HMAC (مطابق للأداة الحالية).
- رسائل الشبكة الحساسة production: يوصى بـ AES-GCM/ChaCha20-Poly1305 عبر مكتبة موثوقة.

## 7) Fairness extension (recommended)
- commit-reveal لseed النرد.
- state hash broadcast كل 5 أحداث.
- alert + terminate ranked match عند hash mismatch المتكرر.
