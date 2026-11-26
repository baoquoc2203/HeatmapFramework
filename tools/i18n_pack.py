#!/usr/bin/env python3
"""Site-wide EN / VI pass for the strings the pages' own i18n does not reach.

Each page already swaps most of its interface through its own TT() / data-en / data-vi hooks.
What is left is text written in one language only: labels inside the embedded panels (the ADA
weekly Wyckoff and 14-day scenario panels came from standalone pages), strings drawn on canvas,
tooltips built at hover time, aria-labels and titles, and generated labels in the signal pages.

This script injects one early <script id="cre-i18n"> into each page. It reads the same site-wide
language key (cre-lang, ?lang= override, default vi) and translates
  * text nodes and title / aria-label / placeholder attributes — now and as the page re-renders
    (MutationObserver), by exact match first, then by pattern rules for generated strings;
  * canvas text, by wrapping fillText / strokeText / measureText so layout measures the
    translated string.
Numbers, dates, tickers and prices are carried through unchanged by the pattern rules; nothing
is computed. Long dated report notes (per-session prose) are not in the dictionaries and stay in
the language the report was written in.

Idempotent: re-running replaces the previous block.
"""
import json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGES = ['index.html', 'robinhood.html', 'ro-signals.html', 'btc-dashboard.html', 'ada-dashboard.html']

# ── VI → EN (shown when the page is in English) ──────────────────────────────────────────
EN = {
  # shared chrome / attributes
  'Điều hướng': 'Navigation', 'Về trang chủ CRE': 'Back to the CRE home page', 'Chức năng': 'Sections',
  'Đổi giao diện sáng / tối': 'Toggle light / dark', 'Giá trị danh mục theo phiên': 'Portfolio value by session',
  'BTC theo phiên': 'BTC by session', 'Sáng / tối': 'Light / dark', 'Xuất CSV': 'Export CSV',
  # robinhood
  '· microcap · mới': '· microcap · new', 'microcap · mới': 'microcap · new', 'MicroDuck (mua lại R1)': 'MicroDuck (re-buy R1)',
  'mua lại': 're-buy', 'meme vừa': 'mid meme', 'người mới': 'newcomer', 'mua lại R1 (giấy)': 're-buy R1 (paper)',
  'đã bán hết': 'sold out', 'chỉ theo dõi': 'watch only', 'Chỉ theo dõi': 'Watch only', 'mở': 'open', 'CÓ': 'YES', 'KHÔNG': 'NO',
  # ro-signals
  'Radar tín hiệu Robinhood Chain': 'Robinhood Chain signal radar', 'Giá đóng cửa': 'Close',
  'Tín hiệu hôm nay': "Today's signals", 'mua mới cho người mới': 'new buys for newcomers',
  'Gần hành động (≤ 10%)': 'Near action (≤ 10%)', 'Hấp dẫn về thống kê': 'Statistically attractive',
  'chưa loại tín hiệu nào có kỳ vọng dương': 'no signal type has positive expectancy yet',
  'Trung tính': 'Neutral', 'Kém thuận lợi': 'Unfavourable', 'về giá vốn dưới 40%': 'back to cost below 40%',
  'Cửa xấu': 'Poor odds', 'bán hết trước ≥ 50%': 'sold out first ≥ 50%',
  'về giá vốn ≥ 40%, bán hết trước < 50%': 'back to cost ≥ 40%, sold out first < 50%',
  'Tất cả': 'All', 'Có thể mua': 'Buyable', 'Đang nắm': 'Holding', 'Theo dõi': 'Watching',
  'Gần hành động và có cửa': 'Near action, with odds', 'Gần hành động nhưng cửa kém': 'Near action, poor odds',
  'Xa hành động, cửa kém': 'Far from action, poor odds', 'Khoảng cách tới hành động gần nhất →': 'Distance to the nearest action →',
  'Tần suất về giá vốn, 30 phiên': 'Back-to-cost frequency, 30 sessions', 'Hấp dẫn (chưa có)': 'Attractive (none yet)',
  'vạch dọc = khoảng tin cậy 90% · dấu * = vị thế giấy hoặc người mới': 'vertical bar = 90% confidence interval · * = paper position or newcomer',
  'Nhìn từ trên': 'Top view', 'Bản đồ 2D': '2D map', 'hôm nay': 'today', 'Hôm nay': 'Today',
  'Không tải được 3D trên thiết bị này: đang hiện bản 2D nhìn từ trên.': '3D could not load on this device: showing the 2D top view.',
  'Hành động kế tiếp': 'Next action', 'Bán hết': 'Sell all', 'Giá vào': 'Entry', 'Chốt 50%': 'Take 50%', 'Cửa thắng': 'Odds',
  'Dòng tiền ĐỎ': 'Flow RED', 'Dòng tiền XANH': 'Flow GREEN', 'Dòng tiền —': 'Flow —', 'Vé số': 'Lottery ticket', 'Lưu ý dữ liệu': 'Data notes',
  'Tất cả tín hiệu': 'All signals', 'Gần hành động nhất': 'Nearest to action', 'Cửa thắng tốt nhất': 'Best odds',
  'Breakout token mới · chỉ theo dõi': 'New-token breakout · watch only', 'Phiên': 'Session',
  'Volume / trung vị 7N': 'Volume / 7D median', 'Vốn hoá': 'Market cap', 'Hiện tại': 'Current',
  'Texel là gì.': 'What Texel is.', 'Ngách:': 'Niche:', 'Token giả:': 'Fake token:',
  'Kiểm lại luật (1)–(4) trên 120 ngày, token native': 'Backtest of rules (1)–(4) over 120 days, native tokens',
  'Chạm ×2 trong 14 phiên': 'Hit ×2 within 14 sessions', 'Mất 50% trong 14 phiên': 'Lost 50% within 14 sessions',
  'âm': 'negative', 'Đọc đúng mức:': 'Read at the right weight:', 'phát hiện sớm': 'early detection',
  'Dòng tiền lệnh lớn & cá voi': 'Large-order flow & whales', 'Giá đóng cửa (thang log)': 'Close (log scale)',
  'Cột: ngày mua ròng (lệnh lớn)': 'Bars: net-buy days (large orders)', 'bán ròng': 'net sell',
  'gần cân bằng (±10%)': 'near balance (±10%)', 'MFI 14 ngày': '14-day MFI',
  '▲▼ cá voi mua / bán ròng bất thường nhất trong khung': '▲▼ most unusual whale net buy / sell in the window',
  'XANH: cân nhắc mua lướt': 'GREEN: consider a short-term buy', 'nền đỏ: lệnh lớn mua đuổi': 'red background: large orders chasing',
  'ĐỎ': 'RED', 'XANH': 'GREEN', 'Lệnh lớn ròng 90 ngày': 'Net large orders, 90 days', 'Lệnh lớn ròng 7 ngày': 'Net large orders, 7 days',
  'Ngày cá voi mua / bán ròng': 'Whale net buy / sell days', 'trung tính (20–80)': 'neutral (20–80)',
  'Ví gom nhiều nhất 30 ngày': 'Top accumulating wallets, 30 days', 'Ví xả nhiều nhất 30 ngày': 'Top distributing wallets, 30 days',
  'Ví': 'Wallet', 'Ròng': 'Net', 'Bán': 'Sell', 'Mua': 'Buy', 'Giá mua TB': 'Avg buy price', 'Ngày ≥ ngưỡng': 'Days ≥ threshold',
  'Giải mã: vì sao “lệnh lớn mua xong là rớt”': 'Decoded: why “large orders buy, then it drops”',
  '1. Lệnh lớn mua đi cùng ngày giá tăng.': '1. Large-order buying comes on up days.',
  '2. Trong một thị trường giảm, đợt hồi bị mua đuổi thường thất bại.': '2. In a falling market, chased rebounds usually fail.',
  '3. Bản thân dòng lệnh lớn không báo trước được hướng đi.': '3. Large-order flow on its own does not predict direction.',
  'Từ đó suy ra tín hiệu XANH là mặt ngược của mua đuổi:': 'Hence the GREEN signal is the mirror image of chasing:',
  'giá hồi lên khi lệnh lớn': 'price rebounds while large orders', 'không': 'do not',
  '% tăng sau 3': '% up after 3', '% tăng sau 7': '% up after 7', 'Mọi ngày (mốc so sánh)': 'All days (baseline)',
  'ĐỎ (mua đuổi)': 'RED (chasing)', 'Cá voi mua ròng mạnh (dấu ▲)': 'Strong whale net buy (▲)',
  'mua lướt, giữ tối đa 3 phiên': 'short-term buy, hold at most 3 sessions', 'không mua': 'no buy',
  'Mức ủng hộ của BTC': 'BTC support level', 'lớp phủ · không đổi lệnh': 'overlay · changes no orders',
  'Ủng hộ': 'Supportive', 'Trung lập': 'Neutral', 'Rủi ro': 'Risk', 'Báo động': 'Alert', 'BÁO ĐỘNG': 'ALERT',
  'Lên Trung lập': 'Up to Neutral', 'Xuống Báo động': 'Down to Alert', 'Danh mục giảm so với BTC': 'Portfolio down vs BTC',
  'trung vị 4 ngày BTC giảm ≥ 2%': 'median of 4 days with BTC down ≥ 2%',
  'Cách đọc radar': 'How to read the radar', 'Bản 3D.': '3D view.', 'Vòng dưới chân mỗi token': 'The ring under each token',
  'Bản đồ 2D.': '2D map.', 'Cửa thắng được tính thế nào': 'How the odds are computed', 'Luật mua và bán': 'Buy and sell rules',
  'Nếu bạn mới bắt đầu': 'If you are just starting', 'Không đạt chuẩn': 'Below standard', 'Đã bật': 'Fired',
  'cửa xấu': 'poor odds', 'kém thuận lợi': 'unfavourable', 'trung tính': 'neutral', 'hấp dẫn': 'attractive',
  'Nhãn theo quy tắc cố định:': 'Labels follow fixed rules:',
  'khi tần suất bán hết trước ≥ 50%;': 'when the sold-out-first frequency is ≥ 50%;',
  'khi tần suất về giá vốn dưới 40%;': 'when the back-to-cost frequency is below 40%;', 'cho phần còn lại;': 'for the rest;',
  'Lọc nhóm': 'Filter groups', 'Bản đồ: khoảng cách tới hành động và tần suất về giá vốn': 'Map: distance to action and back-to-cost frequency',
  'Xoay trái': 'Rotate left', 'Xoay phải': 'Rotate right', 'Token trước': 'Previous token', 'Token sau': 'Next token',
  'Sắp xếp': 'Sort', 'Lớp breakout token mới': 'New-token breakout layer', 'Dòng tiền lệnh lớn và cá voi': 'Large-order flow and whales',
  'Chọn token': 'Choose token', 'Khung thời gian': 'Timeframe', 'Giá BTC 20 phiên và các vùng đổi mức': 'BTC price over 20 sessions and the level-change zones',
  'Xem chi tiết hành động': 'See action details',
  'Gần hành động chưa chắc là cơ hội: radar hiện cả khoảng cách lẫn cửa thắng': 'Near action is not necessarily an opportunity: the radar shows both the distance and the odds',
  'Radar micro là kênh khám phá, không tự động được cấp vốn. Kiểm định 02/11 trên 405 meme RH: lần radar bật đầu tiên 0/8 chạm ×1.5 trong 10 phiên, đối chứng 17%.': 'The micro radar is a discovery channel and is not funded automatically. Test of 02/11 on 405 RH memes: on the first radar fire, 0/8 reached ×1.5 within 10 sessions, against 17% for the control.',
  'Bắt các token native vừa phá đỉnh mạnh trên volume đột biến, kiểu Texel ngày 24/11. Đây là lớp khám phá: không mua, không vào rổ gợi ý, chỉ ghi giấy để chấm (BR-001).': 'Catches native tokens that have just broken out hard on a volume spike, like Texel on 24/11. This is a discovery layer: no buying, not in the suggested basket, recorded on paper only for scoring (BR-001).',
  'Token thuộc vũ trụ quét mới và đủ cả 5 điều kiện ở close ngày: (1) close ≥ 1.5 × close hôm trước; (2) close là mức cao nhất 30 phiên (tính cả từ lúc niêm yết); (3) volume ≥ 3 × trung vị 7 ngày trước và ≥ $50k; (4) vốn hoá $0.1M–$6M; (5) qua cờ cứng: top-10 < 40%, không honeypot. Chấm mỗi lần bật ở +3 và +7 phiên, và xem có chạm ×2 hay mất 50% trong 14 phiên; kết luận sau 20 lần.': 'A token in the new scan universe that meets all 5 conditions at the daily close: (1) close ≥ 1.5 × the previous close; (2) the close is the highest in 30 sessions (counting from listing); (3) volume ≥ 3 × the prior 7-day median and ≥ $50k; (4) market cap $0.1M–$6M; (5) passes the hard flags: top-10 < 40%, not a honeypot. Each fire is scored at +3 and +7 sessions, and checked for hitting ×2 or losing 50% within 14 sessions; a conclusion after 20 fires.',
  'mua ngay sau breakout không tốt hơn mua ngẫu nhiên (trung bình +3 phiên còn tệ hơn ở lượt 1). Nó giống vé số: khoảng 1/3 chạm ×2 trong hai tuần nhưng hơn một nửa mất một nửa giá trị, và từ tháng 10 chưa lần nào chạm ×2. Vì vậy lớp này để': 'buying right after a breakout is no better than buying at random (the +3-session average is even worse in pass 1). It is like a lottery ticket: about 1/3 hit ×2 within two weeks but more than half lose half their value, and since October none has hit ×2. So this layer is for',
  'token mới đáng theo dõi, không phải tín hiệu mua. Hai lượt kiểm chỉ tải được một phần vũ trụ vì giới hạn tần suất của API; kết quả cùng chiều.': 'new tokens worth watching, not a buy signal. The two passes could load only part of the universe because of API rate limits; the results point the same way.',
  'Giá đóng cửa, cột dòng tiền lệnh lớn mỗi ngày, dấu cá voi và Money Flow Index (14 ngày). Lớp theo dõi, không phải tín hiệu: không đổi lệnh nào và chưa được kiểm định có lợi thế.': 'Closes, daily large-order flow bars, whale marks and the Money Flow Index (14 days). A watch layer, not a signal: it changes no orders and has not been shown to have an edge.',
  'Tương quan giữa dòng lệnh lớn ròng và giá cùng ngày là +0.28: lệnh lớn mua nhiều nhất đúng vào những phiên hồi. Họ đang mua đuổi đợt hồi, không mua ở đáy.': 'The correlation between net large-order flow and same-day price is +0.28: large orders buy most on exactly the rebound sessions. They are chasing rebounds, not buying bottoms.',
  'Sau những ngày lệnh lớn 3 ngày mua ròng và giá tăng (nền đỏ), giá 7 phiên sau giảm trung bình −19.8%, chỉ 18% số lần tăng; mức chung của cả mẫu là −15.7% và 27%. Tức là mua đuổi còn tệ hơn mua ngẫu nhiên.': 'After days with 3-day net large-order buying and a rising price (red background), price 7 sessions later fell −19.8% on average, rising only 18% of the time; the whole sample was −15.7% and 27%. So chasing is worse than buying at random.',
  'Tương quan giữa lệnh lớn ròng hôm nay và giá 1, 3, 7 phiên sau gần bằng 0 (+0.03, 0.00, −0.04). Cảm giác “mua xong là rớt” phần lớn đến từ việc cả mẫu đang trong chân giảm: 73% các cửa sổ 7 phiên đều giảm, dù hôm đó lệnh lớn mua hay bán.': "The correlation between today's net large orders and price 1, 3 and 7 sessions later is close to 0 (+0.03, 0.00, −0.04). The feeling of “buy and it drops” comes mostly from the whole sample being in a down leg: 73% of 7-session windows fell, whether large orders bought or sold that day.",
  'đuổi theo, và dòng tiền (MFI) quay lên từ vùng thấp. Cụ thể, XANH khi đủ cả 4: (a) tổng lệnh lớn ròng 3 ngày ≤ 0; (b) close hôm nay cao hơn hôm qua; (c) MFI tăng 2 phiên liền; (d) MFI đã ở ≤ 40 trong 3 phiên gần nhất. ĐỎ khi lệnh lớn ròng 3 ngày > 0 và close tăng.': "chase it, and money flow (MFI) turns up from a low zone. Specifically, GREEN when all 4 hold: (a) 3-day net large orders ≤ 0; (b) today's close above yesterday's; (c) MFI up 2 sessions in a row; (d) MFI was ≤ 40 within the last 3 sessions. RED when 3-day net large orders > 0 and the close rises.",
  'XANH chỉ hơn mốc so sánh trong 1–3 phiên; sau 7 phiên vẫn âm (−11.1%). Vì vậy nó là tín hiệu': 'GREEN beats the baseline only over 1–3 sessions; after 7 sessions it is still negative (−11.1%). So it is a signal for a',
  ', không phải điểm gom dài hạn. Mẫu XANH chỉ có 13 lần và được dựng sau khi đã xem dữ liệu (trong mẫu). Bỏ riêng HMM ra thì kết quả +3 phiên đổi thành −2.2%, tức là chưa vững. ĐỎ có mẫu lớn hơn (104 lần) nên đáng tin hơn như một cảnh báo': ', not a long-term accumulation point. The GREEN sample has only 13 instances and was built after looking at the data (in-sample). Leaving out HMM alone turns the +3-session result into −2.2%, so it is not robust. RED has a larger sample (104 instances), so it is more reliable as a warning',
  'từ close 25/11, mỗi lần XANH bật trên 14 token của bảng tín hiệu được ghi lại và chấm ở +3 phiên so với mốc mọi ngày cùng kỳ. Sau 20 lần mới kết luận có giữ hay bỏ. Trước đó XANH/ĐỎ chỉ để tham khảo, không đổi lệnh nào của danh mục và không thay luật radar.': 'from the 25/11 close, every GREEN fire on the 14 tokens of the signal board is recorded and scored at +3 sessions against the all-days baseline for the same period. Only after 20 fires is it kept or dropped. Until then GREEN/RED is for reference only, changes no portfolio orders and does not replace the radar rules.',
  'Nguồn: CoinGecko onchain, giao dịch theo khoảng thời gian của từng token, gộp mọi pool trên Robinhood Chain. Mua/bán xác định theo token đi ra hay đi vào pool; USD theo giá từng lệnh; bỏ lệnh bị đánh dấu bất thường.': "Source: CoinGecko onchain, trades over each token's time range, all pools on Robinhood Chain combined. Buy/sell is set by whether the token leaves or enters the pool; USD at each trade's price; trades flagged as anomalous are dropped.",
  'Cá voi = một ví (người ký giao dịch) mua ròng hoặc bán ròng trong ngày từ ngưỡng: PONS, CASHCAT, AI ≥ $10k; KITSU ≥ $1k; các token còn lại ≥ $3k. Mua rồi bán lại trong ngày tự triệt tiêu, nên bot quay vòng phần lớn bị loại. Dấu ▲▼ đánh vào 10 ngày (khung 30 ngày: 6 ngày) có cá voi ròng bất thường nhất: cá voi ròng ít nhất gấp đôi ngưỡng, xếp theo tỷ lệ so với trung vị tổng lệnh lớn 14 ngày trước đó (để ngày đầu tháng 9 volume rất lớn không lấn hết các ngày gần đây). Dấu đặt ở giá đóng cửa ngày đó.': "Whale = one wallet (the transaction signer) net buying or net selling in a day above the threshold: PONS, CASHCAT, AI ≥ $10k; KITSU ≥ $1k; other tokens ≥ $3k. Buying and selling back within the day cancels out, so most churning bots are excluded. ▲▼ marks the 10 days (30-day window: 6 days) with the most unusual whale net flow: whale net at least twice the threshold, ranked by its ratio to the median large-order total of the previous 14 days (so the very heavy early-September volume does not crowd out recent days). The mark sits at that day's close.",
  'MFI 14 ngày tính theo công thức chuẩn từ giá cao, thấp, đóng cửa và volume ngày của CoinGecko. Volume CoinGecko của CHUMP đứng quanh $1M/ngày tới 17/11 trong khi lệnh lớn on-chain nhỏ hơn nhiều, nên MFI của CHUMP kém tin cậy.': "14-day MFI uses the standard formula on CoinGecko daily high, low, close and volume. CHUMP's CoinGecko volume sat near $1M/day until 17/11 while on-chain large orders were much smaller, so CHUMP's MFI is less reliable.",
  'Tâm đĩa là hành động ngay; càng xa tâm, giá càng phải đi xa mới tới mức hành động gần nhất (ba vòng: 5%, 20%, 60%). Token nổi trên đĩa cần giá tăng, chìm dưới đĩa cần giá giảm. Màu quả cầu theo nhóm.': 'The centre of the disc is immediate action; the farther from the centre, the farther price must move to reach the nearest action level (three rings: 5%, 20%, 60%). Tokens above the disc need price to rise, those below need it to fall. Sphere colour follows the group.',
  'là cửa thắng: vòng càng rộng thì tần suất quay về giá vốn trong 30 phiên càng cao; màu đỏ là cửa xấu, vàng là kém thuận lợi, xanh dương là trung tính, xanh lá là hấp dẫn về thống kê.': 'is the odds: the wider the ring, the higher the frequency of getting back to cost within 30 sessions; red is poor odds, yellow unfavourable, blue neutral, green statistically attractive.',
  'Trục ngang là khoảng cách tới hành động (trái là gần). Trục dọc là tần suất quay về giá vốn. Viền chấm theo cửa thắng. Token ở góc dưới bên trái là “gần hành động nhưng cửa xấu”.': 'The horizontal axis is distance to action (left is near). The vertical axis is the back-to-cost frequency. Dot outlines follow the odds. Tokens in the bottom-left corner are “near action but poor odds”.',
  'Với mỗi token, lấy mọi token cùng lớp (meme vừa: vốn hoá ≥ $5M và volume TB 7 ngày ≥ $1M; microcap: $0.5–5M) và mọi ngày bắt đầu trong 30 ngày gần nhất mà cửa sổ 30 phiên đã khép (': 'For each token, take every token in the same class (mid meme: market cap ≥ $5M and 7-day average volume ≥ $1M; microcap: $0.5–5M) and every start day in the last 30 days whose 30-session window has closed (',
  '). Đếm xem từ ngày đó, giá có đi được quãng mà token này đang cần hay không, và chạm mức nào trước.': '). Count whether, from that day, price covered the distance this token now needs, and which level it hit first.',
  'Cỡ mẫu tính theo số token độc lập, không theo số ngày: mid meme': 'Sample size counts independent tokens, not days: mid meme',
  'Cỡ mẫu tính theo số token độc lập, không theo số ngày: meme vừa': 'Sample size counts independent tokens, not days: mid meme',
  '. Dưới 15 token thì ghi INSUFFICIENT DATA.': '. Below 15 tokens it reads INSUFFICIENT DATA.',
  'chỉ khi kỳ vọng sau phí của loại tín hiệu đó có cận dưới 90% lớn hơn 0. Hiện chưa loại tín hiệu nào đạt.': 'only when the after-fee expectancy of that signal type has a 90% lower bound above 0. No signal type meets it yet.',
  'Kiểm định walk-forward cho thấy ước lượng theo cohort gần nhất chính xác hơn base rate cả lịch sử, nhưng vẫn cao hơn thực tế khi thị trường yếu dần. Hãy đọc các con số như cận trên. Chi tiết ở mục Bằng chứng trên Bàn quản lý.': 'A walk-forward test shows the most-recent-cohort estimate is more accurate than the full-history base rate, but still above reality as the market weakens. Read the numbers as upper bounds. Details in the Evidence section of the management desk.',
  'Lớp này chỉ để hiển thị. Nó không đổi tín hiệu, thang mua, chốt lời, trailing, quy mô hay luật R1–R5.': 'This layer is display only. It does not change signals, the buy ladder, take-profits, trailing, sizing or rules R1–R5.',
  'Chỉ dùng giá đóng cửa ngày theo UTC (07:00 giờ Việt Nam). Biến động trong ngày không tính.': 'Only UTC daily closes are used (07:00 Vietnam time). Intraday moves do not count.',
  'Meme vừa: mua lần đầu ở ngày đầu tiên giá đóng cửa không in đáy mới kể từ đỉnh. Mua thêm khi giá đóng cửa ≤ 80% giá vốn trung bình, cách lần trước ≥ 3 ngày, tối đa 4 lần.': 'Mid meme: first buy on the first day the close makes no new low since the top. Add when the close is ≤ 80% of the average cost, ≥ 3 days after the previous buy, at most 4 buys.',
  'Microcap ($0.5–5M, đã giảm ≥ 85% từ đỉnh): mua 1 lần khi giá không in đáy mới và volume ngày ≥ 2× trung vị 7 ngày.': 'Microcap ($0.5–5M, down ≥ 85% from the top): buy once when price makes no new low and daily volume is ≥ 2× the 7-day median.',
  'Chốt 50% khi giá gấp đôi giá vốn, rồi bán dần ở ×5, ×10 (microcap thêm ×30, ×100). Phần còn lại thoát khi giá rơi mạnh từ đỉnh.': 'Take 50% when price doubles the cost, then scale out at ×5, ×10 (microcap also ×30, ×100). The rest exits when price falls hard from its peak.',
  'Bán hết khi thanh khoản cạn, 2 close liên tiếp dưới 25% giá vốn, hoặc có rủi ro bảo mật. Đây không phải mức lỗ tối đa được bảo đảm.': 'Sell all when liquidity dries up, on 2 consecutive closes below 25% of cost, or on a security risk. This is not a guaranteed maximum loss.',
  'Giá vốn trong nhóm "Đang nắm" là của danh mục gốc. Nếu mua ở giá khác, tự tính lại: mỗi bậc mua thêm = 80% giá vốn trung bình của bạn, chốt 50% ở 2× giá vốn của bạn. Quy mô gợi ý: 5% vốn meme mỗi lần, tối đa 20% một token, microcap 2%. Mua trễ cho kết quả kém hơn: chờ thêm 2–3 phiên sau tín hiệu làm tỷ lệ lệnh có lãi giảm từ 20.9% xuống 14.6%.': 'The cost in the "Holding" group is the original portfolio\'s. If you bought at a different price, recompute: each add step = 80% of your average cost, take 50% at 2× your cost. Suggested size: 5% of meme capital per buy, at most 20% in one token, microcap 2%. Buying late does worse: waiting 2–3 more sessions after the signal cut the share of winning trades from 20.9% to 14.6%.',
  'Tín hiệu theo luật của một khung phân tích có hệ thống, không phải lời khuyên đầu tư. Hệ thống chưa chứng minh được lợi thế: rổ 12 token gốc giảm 60.6% từ 30/9 đến 29/10 trong khi BTC giảm 6.9%. Token trên Robinhood Chain biến động 10–40% mỗi ngày và có thể mất toàn bộ vốn. Robinhood Markets không phát hành và không bảo trợ các token này. Luôn so khớp toàn bộ địa chỉ contract trước khi giao dịch vì có địa chỉ giả giống phần đầu và đuôi.': 'Rule-based signals from a systematic framework, not investment advice. The system has not proven an edge: the original 12-token basket fell 60.6% from 30/9 to 29/10 while BTC fell 6.9%. Tokens on Robinhood Chain move 10–40% a day and can lose all their value. Robinhood Markets does not issue or endorse these tokens. Always match the full contract address before trading, because fake addresses copy the first and last characters.',
  'Giữ, chưa làm gì': 'Hold, no action',
  'Chưa làm gì': 'No action',
  'Không phụ thuộc mức giá': 'Not tied to a price level',
  'Về giá vốn': 'Back to cost',
  '×1.5 giá vốn': '×1.5 cost',
  '×5 giá vốn': '×5 cost',
  'Chốt 50% (×2), trước mức bán hết': 'Take 50% (×2), before the sell-all level',
  'Chạm mức mua thêm trong 14 phiên': 'Hit the add level within 14 sessions',
  'Bán hết (2 close), trước khi chạm ×2': 'Sell all (2 closes), before hitting ×2',
  'Chạm mốc mua lại trong 14 phiên': 'Hit the re-buy level within 14 sessions',
  'Quay lại đỉnh sau khi thoát': 'Back to the peak after exit',
  'R/R: tới chốt 50% so với tới bán hết': 'R/R: to take-50% vs to sell-all',
  'Số phiên tới ×2 khi chạm': 'Sessions to ×2 when hit',
  'chưa quan sát': 'not observed',
  'Lợi nhuận 30 phiên của analog': 'Analog 30-session return',
  'Có lãi sau 30 phiên': 'In profit after 30 sessions',
  'Đáy trong 30 phiên (so giá hiện tại)': '30-session low (vs current price)',
  'Trường hợp xấu (5%)': 'Bad case (5%)',
  'Loại tín hiệu này từng cho kết quả ra sao': 'How this signal type has performed',
  'Chưa có ước lượng': 'No estimate yet',
  'Thanh khoản: không có dữ liệu': 'Liquidity: no data',
  'Mốc mua lại': 'Re-buy level',
  'Giá vốn': 'Cost',
  'Đỉnh': 'Peak',
  'Mức chốt 50%': 'Take-50% level',
  'Mức bán hết': 'Sell-all level',
  'Chốt lời': 'Take profit',
  'Thoát': 'Exit',
  'Mua lại': 'Re-buy',
  'Chờ': 'Wait',
  'chờ': 'wait',
  'Mua thêm': 'Add',
  'mới': 'new',
  'Meme vừa': 'Mid meme',
  'vòng chân rộng = dễ về giá vốn hơn': 'wider ring = easier to get back to cost',
  'Đã copy địa chỉ contract': 'Contract address copied',
  'Trình duyệt không cho copy tự động': 'The browser blocked automatic copying',
  'Đã xuất CSV': 'CSV exported',
  'Token giả cần tránh': 'Fake token to avoid',
  'Thang người mới': 'Newcomer ladder',
  '◆ Dòng tiền XANH': '◆ Flow GREEN',
  '◆ Dòng tiền ĐỎ': '◆ Flow RED',
  'Token · ngày bật': 'Token · fire date',
  'Close lúc bật': 'Close at fire',
  'Vì sao ở mức này ·': 'Why this level ·',
  'Bàn quản lý': 'Management desk',
  'PONS không thuộc category meme của CoinGecko: dùng analog meme vừa theo giả định.': "PONS is not in CoinGecko's meme category: the mid-meme analog is used as an assumption.",
  'Close CoinGecko 11/11 bị lỗi (×4.7 không kèm volume) nên chuỗi dữ liệu của engine dừng ở 10/11.': "The CoinGecko 11/11 close is faulty (×4.7 with no volume), so the engine's data series stops at 10/11.",
  'Vốn hoá $0.32M, dưới dải micro: dùng analog micro.': 'Market cap $0.32M, below the micro band: the micro analog is used.',
  'XANH · cân nhắc mua lướt': 'GREEN · consider a short-term buy',
  'ĐỎ · đang mua đuổi': 'RED · chasing',
  '◆ XANH: cân nhắc mua lướt (giữ ≤ 3 phiên)': '◆ GREEN: consider a short-term buy (hold ≤ 3 sessions)',
  'Nền đỏ: lệnh lớn đang mua đuổi': 'Red background: large orders are chasing',
  'Thiếu một phần dữ liệu ngày này': "Part of this day's data is missing",
  'vùng quá bán (≤ 20)': 'oversold zone (≤ 20)',
  'vùng quá mua (≥ 80)': 'overbought zone (≥ 80)',
  'Luật hiện tại': 'Current rule',
  'Chỉ mua khi BTC > SMA20': 'Buy only when BTC > SMA20',
  'Chỉ mua khi ≥ 40% token tăng 7 ngày': 'Buy only when ≥ 40% of tokens rose over 7 days',
  'Chờ close cao nhất 3 phiên': 'Wait for a 3-session closing high',
  'Thêm TP0 25% ở ×1.5': 'Add TP0 25% at ×1.5',
  'Không DCA (mua 1 lần)': 'No DCA (single buy)',
  'DCA chỉ khi BTC > SMA20': 'DCA only when BTC > SMA20',
  'Thoát sau 30 phiên nếu chưa ×1.2': 'Exit after 30 sessions if not yet ×1.2',
  'Chỉ mua khi đã giảm ≥ 50%': 'Buy only after a ≥ 50% fall',
  'DCA thưa hơn (≤ 65% giá vốn)': 'Sparser DCA (≤ 65% of cost)',
  'Radar micro hiện tại': 'Current micro radar',
  'Volume ≥ 4× trung vị': 'Volume ≥ 4× median',
  'Chỉ khi BTC > SMA20': 'Only when BTC > SMA20',
  'Chỉ khi đã giảm ≥ 93%': 'Only after a ≥ 93% fall',
  '01/07 → 11/11, mỗi điểm 7 ngày': '01/07 → 11/11, one point per 7 days',
  '×1.5 trong 14 phiên': '×1.5 within 14 sessions',
  '×2 trong 14 phiên': '×2 within 14 sessions',
  '×1.5 trong 30 phiên': '×1.5 within 30 sessions',
  '×2 trong 30 phiên': '×2 within 30 sessions',
  # ADA — 14-day scenario panel
  'Range floor → scenarios — Wyckoff 7–14 ngày tới': 'Range floor → scenarios — Wyckoff, the next 7–14 days',
  '(UTC) · 24/09 → 25/11 thực tế · 26/11 → 10/12 kịch bản': '(UTC) · 24/09 → 25/11 actual · 26/11 → 10/12 scenarios',
  'σ ngày 4.10% (đo 30 phiên)': 'daily σ 4.10% (measured over 30 sessions)',
  'Không phải dự báo — mỗi nhánh gắn với một mức kích hoạt': 'Not a forecast — each branch is tied to a trigger level',
  'Nhánh kịch bản': 'Scenario branches', 'Biên ±1σ': '±1σ band',
  'A · Spring xác nhận': 'A · Spring confirmed', 'B · Giằng co tại đáy': 'B · Chop at the floor', 'C · Thủng đáy → markdown': 'C · Floor breaks → markdown',
  'Ngưỡng xác nhận 0.15614': 'Confirmation level 0.15614', 'Đáy range 0.13883': 'Range floor 0.13883',
  'Kịch bản': 'Scenario', 'Kích hoạt khi': 'Triggers when', 'Vùng ngày 10/12': 'Zone on 10/12', 'Xác suất nền*': 'Base probability*',
  'Ý nghĩa Wyckoff': 'Wyckoff meaning', 'Mất hiệu lực khi': 'Invalidated when', 'Tích cực': 'Positive', 'Theo xu hướng': 'With the trend',
  'Đóng tuần': 'Weekly close', 'hoặc': 'or', 'trên': 'above', 'và': 'and',
  'volume tuần đó vượt 1,716M (trung bình 3 tuần gần nhất). Đáy giữ trên 0.13731.': "that week's volume exceeds 1,716M (the 3-week average). The low holds above 0.13731.",
  '21/11 là spring, 25/11 là test; range 06–11/2026 là một tích lũy lớn hơn và chuyển sang Phase D. Đích gần là mức phủ định cũ 0.17173, giờ là kháng cự.':
    '21/11 is the spring, 25/11 the test; the 06–11/2026 range is a larger accumulation moving into Phase D. The near target is the old invalidation level 0.17173, now resistance.',
  'Đóng ngày dưới 0.13731 → chuyển B.': 'Daily close below 0.13731 → switch to B.',
  'Không có phiên đóng tuần trên 0.15614 hay dưới 0.13883; giá kẹt trong 0.139–0.156.': 'No weekly close above 0.15614 or below 0.13883; price stuck in 0.139–0.156.',
  'Phase C chưa có kết quả: cung đã cạn nhưng cầu chưa xuất hiện. Có thể kéo dài nhiều tuần.': 'Phase C unresolved: supply has dried up but demand has not appeared. It can last for weeks.',
  'Đóng ngày dưới 0.13883 → nghiêng C.': 'Daily close below 0.13883 → leans C.', 'Đóng tuần dưới': 'Weekly close below',
  'Phase E của tái phân phối: 21/11 không phải spring mà là bước đầu của cú phá. Dưới 0.13471 không còn mức hỗ trợ nào trong dữ liệu 2024–2026, nên đáy vùng (0.1249) là biên −1σ, không phải mức trên chart.':
    'Phase E of a re-distribution: 21/11 is not a spring but the first step of the break. Below 0.13471 there is no support level in the 2024–2026 data, so the zone floor (0.1249) is the −1σ band, not a level on the chart.',
  'Đóng tuần lại trên 0.13883 → quay về B.': 'Weekly close back above 0.13883 → back to B.',
  'Hành trình Wyckoff từng ngày · 26/09 → 25/11': 'Day-by-day Wyckoff journey · 26/09 → 25/11',
  'Ngày': 'Date', 'Nhãn': 'Label', 'Giá': 'Price', 'Bằng chứng': 'Evidence', 'Ý nghĩa': 'Meaning',
  'Đỉnh mới trên 0.25429, phiên sau đóng cửa thấp hơn.': 'New high above 0.25429; the next session closed lower.',
  'Upthrust trong range: vượt đỉnh nhưng không giữ được.': 'Upthrust inside the range: broke the high but could not hold it.',
  'Phá vỡ giả': 'False breakout',
  'Phiên tạo ra "đóng tuần xác nhận" trên 0.25429, nhưng volume 277M': 'The session that produced the "confirming weekly close" above 0.25429, but volume 277M was the',
  'thấp nhất': 'lowest', 'đợt 21/09–11/10.': 'of the 21/09–11/10 run.',
  'Phá vỡ không có cầu — cảnh báo tôi đã bỏ lỡ.': 'A breakout without demand — the warning I missed.',
  'Volume 05/10 cao nhất từ 22/08; 06/10 đóng cửa ở 14% biên độ nến.': 'Volume on 05/10 the highest since 22/08; 06/10 closed at 14% of the candle range.',
  'Cú bẫy mua cuối cùng, đỉnh của cả range.': 'The final buying trap, the top of the whole range.',
  'Rơi 19.3% trong 2 ngày, quay lại dưới 0.25429; volume chưa mở rộng.': 'Fell 19.3% in 2 days, back below 0.25429; volume not yet expanding.',
  'Dấu hiệu yếu đầu tiên.': 'The first sign of weakness.',
  'Hồi về vùng 0.25429–0.26177 rồi thất bại; đỉnh thấp hơn UTAD 8.2%, volume giảm.': 'Rallied back to 0.25429–0.26177 and failed; a high 8.2% below the UTAD, on falling volume.',
  ': từ đây giá chỉ tạo đỉnh thấp dần.': ': from here price only makes lower highs.',
  'Đỉnh thấp hơn 10/10 thêm 10.7%.': 'A high another 10.7% below 10/10.', 'Mỗi nhịp hồi thấp hơn nhịp trước.': 'Each rally lower than the last.',
  'Mất 0.20882': 'Lost 0.20882', 'Phiên đầu tiên đóng dưới trần range cũ.': 'The first close below the old range ceiling.',
  'Kịch bản C ngày 01/10 kích hoạt.': 'Scenario C of 01/10 triggered.', 'Thủng 0.19103 với volume tăng.': 'Broke 0.19103 on rising volume.',
  'Cung mở rộng khi phá hỗ trợ.': 'Supply expanding as support breaks.',
  'Hồi lên 0.19985, dưới trần range cũ 0.20882; phiên sau đóng 0.18079 (−9.5%).': 'Rallied to 0.19985, under the old range ceiling 0.20882; the next session closed 0.18079 (−9.5%).',
  'Nhịp hồi thứ ba thấp dần. Cái tôi gọi là "ST?" hôm 04/11 hoá ra là một LPSY.': 'The third lower rally. What I called "ST?" on 04/11 turned out to be an LPSY.',
  'Chạm sát mức phủ định rồi giữ; volume thấp nhất trong 63 phiên.': 'Touched just above the invalidation level and held; the lowest volume in 63 sessions.',
  'Cung cạn ngay trên hỗ trợ — nhưng không có cầu theo sau.': 'Supply dried up right above support — but no demand followed.',
  '13/11 đóng dưới 0.17173; 14/11 rơi 13.4% trong một phiên.': '13/11 closed below 0.17173; 14/11 fell 13.4% in one session.',
  'Mức phân xử bị phá. Volume không bùng nổ: cầu rút đi hơn là cung tháo chạy.': 'The deciding level broke. Volume did not explode: demand withdrew rather than supply fleeing.',
  'Đóng tuần 0.15463': 'Weekly close 0.15463',
  'Volume cao nhất kể từ 30/10; phiên bật 6.8%. Đóng tuần dưới 0.17173.': 'The highest volume since 30/10; a 6.8% bounce session. Weekly close below 0.17173.',
  'Kịch bản C kích hoạt, luận điểm tích lũy bị phủ định.': 'Scenario C triggered; the accumulation thesis is invalidated.',
  'Hồi yếu': 'Weak rally', 'Bốn phiên liền đỉnh quanh 0.155.': 'Four sessions in a row topping near 0.155.',
  'Đáy Phase B cũ 0.15417 đã thành kháng cự.': 'The old Phase B low 0.15417 has become resistance.',
  'Thủng đáy range 0.13883 3.0% trong phiên rồi đóng lại phía trên; volume cao thứ hai từ 31/10.': 'Broke the 0.13883 range floor by 3.0% intraday, then closed back above it; the second-highest volume since 31/10.',
  'Chữ ký của spring hoặc shakeout — nhưng cũng là hình dạng thường thấy ngay trước khi hỗ trợ gãy.': 'The signature of a spring or shakeout — but also the shape often seen just before support gives way.',
  'Hồi': 'Rally', 'Hồi lên vùng 0.154 rồi thất bại.': 'Rallied to the 0.154 area and failed.', 'Kháng cự 0.154–0.156 giữ nguyên.': 'Resistance at 0.154–0.156 holds.',
  'Đáy cao hơn 21/11 1.9%, volume giảm còn một nửa. Nến chưa đóng.': 'A low 1.9% above 21/11, volume halved. Candle not yet closed.',
  'Đúng mẫu "test của spring" — chỉ có giá trị nếu sau đó giá vượt 0.15614 với volume tăng.': 'A textbook "test of the spring" — it only counts if price then clears 0.15614 on rising volume.',
  'Chấm điểm kịch bản · 04/11 → 19/11 · 01/10 → 15/10': 'Scenario scoring · 04/11 → 19/11 · 01/10 → 15/10',
  'Chấm điểm kịch bản 04/11 → 19/11': 'Scenario scoring 04/11 → 19/11', 'Chấm điểm kịch bản 01/10 → 15/10': 'Scenario scoring 01/10 → 15/10',
  '· đóng ngày $0.18079 < $0.18539 → A mất hiệu lực,': '· daily close $0.18079 < $0.18539 → A invalidated,', 'chuyển B': 'switch to B',
  '· đóng tuần $0.17457 — giữ trên $0.17173 chỉ 1.7%.': '· weekly close $0.17457 — held above $0.17173 by only 1.7%.',
  '· đóng ngày $0.16717 < $0.17173 →': '· daily close $0.16717 < $0.17173 →', 'nghiêng C': 'leans C',
  '· đóng tuần $0.15463 < $0.17173 →': '· weekly close $0.15463 < $0.17173 →', 'C kích hoạt': 'C triggered',
  '. Theo đúng quy tắc tôi đặt ra, luận điểm tích lũy bị phủ định.': '. By the rule I set, the accumulation thesis is invalidated.',
  '(mốc) · đóng $0.15137 —': '(checkpoint) · close $0.15137 —', 'dưới cả ba vùng': 'below all three zones',
  ', thấp hơn đáy vùng C 1.8%. Xác suất nền cho kết quả này chỉ khoảng 2.0%.': ', 1.8% under the floor of zone C. The base probability of that outcome was only about 2.0%.',
  'Bài học:': 'Lesson:',
  'hai lần liên tiếp, kịch bản tôi gọi là "cơ sở" đều lạc quan hơn thị trường. Lần này tôi không chọn kịch bản cơ sở theo cảm tính; xếp hạng bên dưới đi theo xu hướng.':
    'twice in a row, the scenario I called "base" was more optimistic than the market. This time I do not pick a base case by feel; the ranking below follows the trend.',
  '· đóng tuần $0.26202 > $0.25429 →': '· weekly close $0.26202 > $0.25429 →', 'A kích hoạt': 'A triggered',
  '. 06/10 lên $0.2794, chạm vùng đích A ($0.26177–$0.28706).': '. 06/10 rose to $0.2794, reaching target zone A ($0.26177–$0.28706).',
  'Nhưng tiêu chí "xác nhận mạnh hơn" — volume tuần vượt 4,112M —': 'But the "stronger confirmation" criterion — weekly volume above 4,112M —',
  'không đạt': 'was not met', ': tuần kích hoạt chỉ 3,500M.': ': the trigger week had only 3,500M.',
  '· đóng ngày $0.23456 < $0.24051 → A mất hiệu lực,': '· daily close $0.23456 < $0.24051 → A invalidated,',
  '(mốc 14 ngày) · đóng $0.2305 → nằm trong vùng B.': '(14-day checkpoint) · close $0.2305 → inside zone B.',
  '· đóng ngày $0.22579 < $0.22721 →': '· daily close $0.22579 < $0.22721 →', '· đóng tuần $0.20505 < $0.20882 →': '· weekly close $0.20505 < $0.20882 →',
  ', rồi giá xuyên qua cả vùng C xuống $0.18539.': ', then price cut through all of zone C down to $0.18539.',
  'một phiên đóng tuần vượt ngưỡng 3% mà volume thấp hơn tuần SOS gốc là xác nhận giả. Các mức chuyển kịch bản báo đúng thứ tự A → B → C, nhưng chỉ sau khi giá đã rơi 16% từ đỉnh. Lần này tôi gắn điều kiện volume vào ngay mức kích hoạt.':
    'a weekly close 3% past the level on lower volume than the original SOS week is a false confirmation. The switch levels called A → B → C in the right order, but only after price had fallen 16% from the top. This time the volume condition is attached to the trigger itself.',
  # ADA — canvases
  'BU/LPS (thủng)': 'BU/LPS (broken)', 'KỊCH BẢN 14 NGÀY': '14-DAY SCENARIOS', 'Phase D · tái phân phối': 'Phase D · re-distribution',
  'Nến hiện tại 25/11 (UTC)': 'Current candle 25/11 (UTC)', 'giá trị nhánh chỉ minh hoạ': 'branch values are illustrative only',
}

EN_RULES = [  # [regex, replacement] — generated strings; numbers pass through
  ['^Lệnh lớn: mua (\\S+), bán (\\S+) → (\\S+)$', 'Large orders: buy $1, sell $2 → $3'],
  ['^Cá voi \\(ví ròng ≥ (\\S+)\\): (\\S+) · ★ dấu cá voi$', 'Whales (wallet net ≥ $1): $2 · ★ whale mark'],
  ['^Cá voi \\(ví ròng ≥ (\\S+)\\): (\\S+)$', 'Whales (wallet net ≥ $1): $2'],
  ['^Thoát phần còn lại nếu giá đóng cửa ≤ (\\S+)$', 'Exit the rest if close ≤ $1'],
  ['^Bán hết nếu 2 giá đóng cửa ≤ (\\S+)$', 'Sell all on 2 closes ≤ $1'],
  ['^(.+) · mới$', '$1 · new'],
  ['^Vốn hoá đã xuống (\\S+) nên analog là microcap; luật vị thế vẫn là meme vừa lúc vào\\.$', 'Market cap has fallen to $1, so the analog is microcap; the position rules stay mid meme as at entry.'],
  ['^Crypto\\.com close (\\S+); cấu trúc theo báo cáo BTC (\\S+) \\((.+), engine kết nối\\)$', 'Crypto.com close $1; structure per BTC report $2 ($3, engine connected)'],
  ['^Kiểm lại trên (\\d+) token × (\\d+) ngày \\(([^,()]+), giữ nguyên như lúc đăng ký\\)$', 'Backtest on $1 tokens × $2 days ($3, unchanged since registration)'],
  [r'^Chốt 50% khi giá đóng cửa ≥ (\S+)$', 'Take 50% when close ≥ $1'],
  [r'^Mua thêm khi giá đóng cửa ≤ (\S+)$', 'Add when close ≤ $1'],
  [r'^Xét mua lại khi giá đóng cửa ≤ (\S+), rồi có close không in đáy mới$', 'Consider re-buying when close ≤ $1, then a close with no new low'],
  [r'^Mua (\d+) lần ở (\S+) \(giá đóng cửa hôm nay\)$', "Buy $1× at $2 (today's close)"],
  [r'^Đã bật ở giá đóng cửa (\S+)$', 'Fired at the $1 close'],
  [r'^về vốn (\S+) · bán hết trước (\S+)$', 'back to cost $1 · sold out first $2'],
  [r'^meme vừa (\d/\d)$', 'mid meme $1'], [r'^mua lại (\d/\d)$', 're-buy $1'], [r'^người mới (\d/\d)$', 'newcomer $1'],
  [r'^(\d+) trong số đó có cửa kém hoặc xấu$', '$1 of them with poor or bad odds'],
  [r'^Lượt (\d+) \(([\d/,]+) token tải được\)$', 'Pass $1 ($2 tokens loaded)'],
  [r'^Lượt (\d+) \(([\d,]+) token\)$', 'Pass $1 ($2 tokens)'],
  [r'^Mốc so sánh lượt (\d+)$', 'Pass $1 baseline'],
  [r'^Mốc so sánh lượt (\d+): mọi ngày vốn hoá (.+), volume ≥ (.+)$', 'Pass $1 baseline: every day with market cap $2, volume ≥ $3'],
  [r'^Chỉ các lần từ (\S+) \(cả hai lượt\)$', 'Only instances from $1 (both passes)'],
  [r'^(\d+) lần$', '$1 times'], [r'^\+(\d+) phiên$', '+$1 sessions'],
  [r'^ngưỡng mỗi lệnh ≥ (.+)$', 'threshold per order ≥ $1'],
  [r'^cá voi ròng (.+) trong (\d+) ngày$', 'whales net $1 over $2 days'],
  [r'^Kiểm lại trên (\d+) token × (\d+) ngày \((.+)\)$', 'Backtest on $1 tokens × $2 days ($3)'],
  [r'^Kiểm tra tiến \((.+), đăng ký (.+)\):$', 'Forward test ($1, registered $2):'],
  [r'^Kiểm tra (\d\d/\d\d)$', 'Check $1'],
  [r'^Luật (\S+) \(đăng ký (\S+), trước khi chấm\)$', 'Rule $1 (registered $2, before scoring)'],
  [r'^(\d+) token \(([\d,]+) ngày-token\)$', '$1 tokens ($2 token-days)'],
  [r'^Tín hiệu dòng tiền lớn ở close (\S+)$', 'Large-flow signal at the $1 close'],
  [r'^(\S+): giá, dòng tiền lệnh lớn, cá voi và MFI (\d+) ngày$', '$1: price, large-order flow, whales and MFI, $2 days'],
  [r'^· (\S+) · Bán hết \((.+)\)$', '· $1 · Sold all ($2)'],
  [r'^· (\S+) · Bán phần còn lại \((.+)\)$', '· $1 · Sold the rest ($2)'],
  [r'^Rổ (\d+) token gốc kém BTC từ (\S+) đến (\S+)$', 'The original $1-token basket underperforms BTC from $2 to $3'],
  [r'^Số token dưới close (\S+): (.+) / dư$', 'Tokens below the $1 close: $2 / remainder'],
  [r'^(\S+) có (\d+) close liên tiếp ≥ (\S+)$', '$1 makes $2 consecutive closes ≥ $3'],
  [r'^≥1 trong (\d+) meme RH lớn nhất có close ≥ 2× giá (\S+)$', '≥1 of the $1 largest RH memes closes ≥ 2× its $2 price'],
  [r'^≥1 trong (\d+) token (\S+) chạm mục tiêu (\S+)$', '≥1 of the $1 $2 tokens hits target $3'],
  [r'^≥1 trong (\S+) chạm mức chốt lời ×2$', '≥1 of $1 hits the ×2 take-profit'],
  [r'^(\S+) có close ≥ (\S+) \(×2 giá vốn\)$', '$1 closes ≥ $2 (×2 cost)'],
  [r'^Đóng tuần (\d\d/\d\d)$', 'Weekly close $1'],
  [r'^Trần range cũ(\s+)(\S+)$', 'Old range ceiling$1$2'],
  [r'^Mức phủ định cũ — thủng (\S+)(\s+)(\S+)$', 'Old invalidation level — broken $1$2$3'],
  [r'^NGƯỠNG XÁC NHẬN SPRING(\s+)(\S+) · đóng tuần$', 'SPRING CONFIRMATION$1$2 · weekly close'],
  [r'^ĐÁY RANGE (\S+)(\s+)(\S+) · đóng tuần$', 'RANGE FLOOR $1$2$3 · weekly close'],
  [r'^Spring\? (\S+) · đáy chu kỳ(\s+)(\S+)$', 'Spring? $1 · cycle low$2$3'],
  [r'^(.+) · ngày \+(\d+) \(kịch bản\)$', '$1 · day +$2 (scenario)'],
  [r'^Close (\S+) · nguồn (.+)$', 'Close $1 · source $2'],
  [r'^là xác suất giá đóng ngày (\S+) nằm trong vùng đó$', 'is the probability that the $1 daily close lands in that zone'],
]

EN_PHRASE = [  # composite text nodes: applied in order of length; kept only when no Vietnamese is left
  ['Đủ 4 điều kiện XANH hôm nay. Nếu vào, coi là lệnh lướt: giữ tối đa 3 phiên, không bình quân giá.', 'All 4 GREEN conditions are met today. If you enter, treat it as a short-term trade: hold at most 3 sessions, no averaging down.'],
  ['Lệnh lớn 3 ngày đang mua ròng và giá vừa tăng: đây là kiểu ngày mà sau đó giá thường giảm thêm. Không mua đuổi.', '3-day large orders are net buying and price just rose: the kind of day after which price usually falls further. Do not chase.'],
  ['Không có tín hiệu XANH hay ĐỎ hôm nay.', 'No GREEN or RED signal today.'],
  ['XANH gần nhất: ', 'Last GREEN: '],
  ['Chưa có XANH trong ', 'No GREEN in the '],
  [' ngày có dữ liệu.', ' days with data.'],
  ['; sau ', '; after '],
  ['Lệnh lớn ròng ', 'Net large orders, '],
  [' ngày (có dữ liệu)', ' days (with data)'],
  ['▲ Giá cần tăng ', '▲ Price needs to rise '],
  ['▼ Giá cần giảm ', '▼ Price needs to fall '],
  ['▲ cần tăng ', '▲ needs to rise '],
  ['▼ cần giảm ', '▼ needs to fall '],
  [' · về giá vốn ', ' · back to cost '],
  [' · bán hết trước ', ' · sold out first '],
  ['Cửa thắng 30 phiên, analog ', '30-session odds, analog '],
  ['meme vừa', 'mid meme'],
  ['trung vị ', 'median '],
  [' trung vị', ' median'],
  [' số ngày', ' of days'],
  ['Mẫu mỏng', 'Thin sample'],
  ['Tin cậy khá', 'Fairly reliable'],
  ['Tin cậy vừa', 'Moderately reliable'],
  ['Thanh khoản rất thấp', 'Very low liquidity'],
  ['Thanh khoản thấp', 'Low liquidity'],
  ['Thanh khoản vừa', 'Moderate liquidity'],
  ['Thanh khoản tốt', 'Good liquidity'],
  ['/ngày', '/day'],
  ['Vốn hoá ', 'Market cap '],
  [' từ đỉnh', ' from peak'],
  ['Mua lần đầu meme vừa', 'Mid-meme first buy'],
  [' lệnh trên ', ' trades on '],
  [' token, sau phí: ', ' tokens, after fees: '],
  ['% có lãi, kỳ vọng ', '% profitable, expectancy '],
  [' trên mỗi đô đã vào (KTC 90% ', ' per dollar invested (90% CI '],
  [' đến ', ' to '],
  ['% chạm ×2 (trung vị ', '% hit ×2 (median '],
  [' phiên), ', ' sessions), '],
  ['% bị bán hết; đáy trung vị ×', '% were sold out; median low ×'],
  [' giá vào. ', ' of entry. '],
  ['Thang mục tiêu sau tín hiệu: INSUFFICIENT DATA (', 'Target ladder after the signal: INSUFFICIENT DATA ('],
  [' lệnh đủ 30 phiên).', ' trades with a full 30 sessions).'],
  ['Trong ', 'Of '],
  [' lệnh đủ 30 phiên: ', ' trades with a full 30 sessions: '],
  [' chạm ×', ' hit ×'],
  ['Kiểm lại trên lịch sử Robinhood Chain (sau phí): tín hiệu mua lần đầu của meme vừa có ', 'Backtest on Robinhood Chain history (after fees): the mid-meme first-buy signal has '],
  [' lệnh, ', ' trades, '],
  ['. Chưa có bằng chứng về lợi thế.', '. No evidence of an edge yet.'],
  [' giá vốn mới', ' new cost'], ['chờ ', 'wait '],
  [' phiên', ' sessions'],
  [' ngày', ' days'],
  [' · nguồn ', ' · source '],
  ['(mới bật)', '(just fired)'],
]

EN_SUB = [  # phrase swaps for short generated strings and attributes (longest first)
  ['Di chuột hoặc kéo ngón tay để xem token; chạm để ghim', 'Hover or drag a finger to see a token; tap to pin'],
  ['P(về giá vốn trong 30 phiên)', 'P(back to cost within 30 sessions)'], ['KTC 90%', '90% CI'],
  [' tới hành động, về giá vốn ', ' to action, back to cost '], ['Bán hết trước ', 'Sold out first '],
  [', chạm ×2 trước ', ', hit ×2 first '], [', về giá vốn ', ', back to cost '],
  ['mua lại R1 (giấy)', 're-buy R1 (paper)'], ['người mới', 'newcomer'], ['meme vừa', 'mid meme'], ['mua lại', 're-buy'],
  ['đã bán hết', 'sold out'], ['Mức ủng hộ của BTC: ', 'BTC support level: '], ['Báo động', 'Alert'], ['Rủi ro', 'Risk'],
  ['Trung lập', 'Neutral'], ['Ủng hộ', 'Supportive'],
  ['bán hết sau 2 close dưới mức', 'sold all after 2 closes below the level'], ['mở, đủ 4 lần (giá vốn ', 'open, all 4 buys (cost '],
  ['(giấy vì R5 bật)', '(paper because R5 is on)'], ['(vé số, giấy; volume mỏng)', '(lottery ticket, paper; thin volume)'], ['(vé số, giấy)', '(lottery ticket, paper)'], ['TP0 giấy', 'TP0 paper'],
  ['đã đóng ', 'closed '], ['mở từ ', 'open since '], ['mở ', 'opened '], [' chạm ', ' hit '], [' ở ', ' at '],
  [' (diễn giải)', ' (interpretive)'], ['ngày-token', 'token-days'], ['kéo bằng chuột để xoay bản 3D', 'drag with the mouse to rotate the 3D view'],
]

# ── EN → VI (shown when the page is in Vietnamese) ───────────────────────────────────────
VI = {
  'Home': 'Trang chủ', 'Tracked assets': 'Tài sản theo dõi', 'copy': 'sao chép', 'Copy': 'Sao chép',
  # heatmap toolbar / legend / SVG row labels
  'Layers': 'Lớp', 'Zoom': 'Thu phóng', 'Reset': 'Đặt lại', 'Scale': 'Thang', 'Linear': 'Tuyến tính', 'Bands': 'Dải',
  'Context Layer': 'Lớp bối cảnh', 'Spine 24m (canonical)': 'Spine 24 tháng (chuẩn)',
  'Fear & Greed (BTC-correlated):': 'Fear & Greed (tương quan BTC):', 'Fear & Greed:': 'Fear & Greed:',
  'Extreme fear': 'Sợ hãi tột độ', 'Fear': 'Sợ hãi', 'Neutral': 'Trung lập', 'Greed': 'Tham lam', 'Extreme greed': 'Tham lam tột độ',
  'Mercury Rx / Shmita (on)': 'Mercury Rx / Shmita (bật)', 'ADA price': 'Giá ADA', 'BTC price': 'Giá BTC',
  'Nov 25 cone:': 'Cone 25/11:', '5th / 95th percentile': 'phân vị 5 / 95', 'central 50% (25th–75th)': '50% giữa (phân vị 25–75)',
  'median — flat, driftless by construction': 'trung vị — phẳng, không trôi theo cách dựng',
  '⚠ p75–95 — flag, not a sell signal': '⚠ p75–95 — cờ cảnh báo, không phải tín hiệu bán', 'p50 median ratio': 'tỷ lệ trung vị p50',
  'tracked calls from Jun 12': 'theo dõi từ 12/06', 'tracked calls from Jul 1': 'theo dõi từ 01/07',
  'retro→tracked': 'hồi tố→theo dõi', 'calendar': 'lịch', 'crypto-wide': 'toàn thị trường', 'real index': 'chỉ số thật',
  # heatmap tooltip
  'Cycle thesis': 'Luận điểm chu kỳ', 'Context band': 'Dải bối cảnh', '50% range': 'Vùng 50%', 'median (flat)': 'trung vị (phẳng)',
  'within': 'trong vùng', 'Nov 25 cone': 'Cone 25/11', 'n/a (future)': 'chưa có (tương lai)', 'not verified': 'chưa xác minh',
  'n/a (pre-2018)': 'chưa có (trước 2018)', 'n/a': 'chưa có',
  # weekly Wyckoff panel
  'Wyckoff cycle — events & phases': 'Chu kỳ Wyckoff — sự kiện & pha', 'weekly': 'tuần', 'daily': 'ngày',
  '· Jan 2024 → 23 Nov 2026 · schematic layout after Bogomazov / Pruden ·': '· 01/2024 → 23/11/2026 · bố cục sơ đồ theo Bogomazov / Pruden ·',
  'Nov 25 vintage': 'bản 25/11', 'CoinGecko · 152 weekly bars · live spot': 'CoinGecko · 152 nến tuần · giá trực tiếp',
  'separate feed from the monthly Crypto.com series above': 'nguồn riêng, tách khỏi chuỗi tháng Crypto.com phía trên',
  'Swing line': 'Đường swing', 'Candles': 'Nến', 'Event labels': 'Nhãn sự kiện', 'Support / Resistance': 'Hỗ trợ / Kháng cự',
  'Phases': 'Pha', 'Volume': 'Khối lượng', 'Full range': 'Toàn bộ', 'Cycle stage:': 'Giai đoạn chu kỳ:',
  'Base / Accumulation': 'Nền / Accumulation', 'event confirmed by price & volume signature': 'sự kiện có chữ ký giá & khối lượng',
  'event is interpretive': 'sự kiện mang tính diễn giải', 'Support / resistance': 'Hỗ trợ / kháng cự',
  'Swing line — ZigZag on real weekly highs/lows, 16%': 'Đường swing — ZigZag trên high/low tuần thật, 16%',
  'Resistance': 'Kháng cự', 'Support': 'Hỗ trợ', 'Lines': 'Đường', 'Base low': 'Đáy nền',
  # robinhood / ro-signals
  'Market backdrop': 'Bối cảnh thị trường', 'Monthly map': 'Bản đồ tháng',
  'Nov 25 Levels': 'Mức 25/11', 'Nov 25 Levels + Zones': 'Mức + vùng 25/11', "Live (Nov'26)": 'Hiện tại (11/26)',
  '2017–Now': '2017–nay', '2014–Now': '2014–nay',
}

VI_RULES = [
  [r'^(.*?)· week in progress$', '$1· tuần đang chạy'],
  [r'^Week of (.+)$', 'Tuần $1'],
]
VI_SUB = [
  ['Spine is fixed at 24m.', 'Spine cố định ở 24 tháng.'],
]

JS = r'''<script id="cre-i18n">
/* CRE i18n pass — see tools/i18n_pack.py. Translates what the page's own TT()/data-en hooks miss:
   embedded-panel labels, canvas text, hover tooltips, aria-labels, generated signal labels. */
(function(){
  var L; try{ var u=new URLSearchParams(location.search).get('lang'); L=(u==='en'||u==='vi')?u:(localStorage.getItem('cre-lang')==='en'?'en':'vi'); }catch(e){ L='vi'; }
  var D=__DATA__, M=D[L].map, R=D[L].rules.map(function(r){return [new RegExp(r[0]),r[1]];}), S=D[L].sub, F=D[L].phrase||[], C=new Map();
  var VIR=/[ăâđêôơưạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹáàãéèíìóòõúùýĂÂĐÊÔƠƯ]/i;
  function tr(s,attr){
    if(s==null) return s; s=String(s); var t=s.trim(); if(!t) return s;
    if(C.has(t)){ var c=C.get(t); return c===t?s:s.replace(t,c); }
    var o=Object.prototype.hasOwnProperty.call(M,t)?M[t]:null;
    if(o==null){ o=t; for(var i=0;i<R.length;i++){ if(R[i][0].test(o)){ o=o.replace(R[i][0],R[i][1]); break; } } }
    if(o===t&&attr){ for(var j=0;j<S.length;j++){ if(o.indexOf(S[j][0])>-1) o=o.split(S[j][0]).join(S[j][1]); } }
    if(o===t&&!attr&&F.length&&(L!=='en'||VIR.test(t))){ var q=t; for(var k=0;k<F.length;k++){ if(q.indexOf(F[k][0])>-1) q=q.split(F[k][0]).join(F[k][1]); }
      if(q!==t&&(L!=='en'||!VIR.test(q))) o=q; }
    if(C.size<5000) C.set(t,o);
    return o===t?s:s.replace(t,o);
  }
  window.__creTr=tr;
  var P=window.CanvasRenderingContext2D&&CanvasRenderingContext2D.prototype;
  if(P) ['fillText','strokeText','measureText'].forEach(function(k){ var f=P[k]; P[k]=function(){ if(arguments.length) arguments[0]=tr(arguments[0]); return f.apply(this,arguments); }; });
  var A=['title','aria-label','placeholder'];
  function txt(n){ var p=n.parentNode; if(!p||/^(SCRIPT|STYLE|TEXTAREA)$/.test(p.nodeName)) return; var v=n.nodeValue, w=tr(v); if(w!==v) n.nodeValue=w; }
  function att(e){ for(var i=0;i<A.length;i++){ var v=e.getAttribute&&e.getAttribute(A[i]); if(v){ var w=tr(v,1); if(w!==v) e.setAttribute(A[i],w); } } }
  function walk(r){
    if(r.nodeType===3){ txt(r); return; } if(r.nodeType!==1) return;
    if(/^(SCRIPT|STYLE)$/.test(r.nodeName)) return; att(r);
    var it=document.createTreeWalker(r,NodeFilter.SHOW_TEXT|NodeFilter.SHOW_ELEMENT), n;
    while((n=it.nextNode())){ if(n.nodeType===3) txt(n); else att(n); }
  }
  function start(){
    document.documentElement.lang=L; walk(document.body);
    new MutationObserver(function(ms){ ms.forEach(function(m){
      if(m.type==='characterData') txt(m.target);
      else if(m.type==='attributes') att(m.target);
      else m.addedNodes.forEach(walk);
    }); }).observe(document.body,{subtree:true,childList:true,characterData:true,attributes:true,attributeFilter:A});
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',start); else start();
})();
</script>'''


def build():
    data = {'en': {'map': EN, 'rules': EN_RULES, 'sub': sorted(EN_SUB, key=lambda p: -len(p[0])), 'phrase': sorted(EN_PHRASE, key=lambda p: -len(p[0]))},
            'vi': {'map': VI, 'rules': VI_RULES, 'sub': VI_SUB}}
    # JS regex replacement uses $1; Python-side patterns are written for JS directly
    return JS.replace('__DATA__', json.dumps(data, ensure_ascii=False))


def main():
    block = build()
    for name in PAGES:
        p = ROOT / name
        s = p.read_text(encoding='utf-8')
        s = re.sub(r'\n?<script id="cre-i18n">.*?</script>', '', s, flags=re.S)
        i = s.index('<head>') + len('<head>') if '<head>' in s else s.index('<head ')
        if '<head>' not in s:
            i = s.index('>', i) + 1
        s = s[:i] + '\n' + block + s[i:]
        p.write_text(s, encoding='utf-8')
        print(name, 'i18n pass')


if __name__ == '__main__':
    main()
