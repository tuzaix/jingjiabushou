# 数据库性能优化方案 - `market_service.py`

针对 `market_service.py` 模块中的 SQL 查询分析，以下是提升性能的索引优化方案。该方案主要围绕高频查询表 `call_auction_data`、`yesterday_limit_up` 以及辅助表进行设计。

## 1. 核心表：`call_auction_data` (竞价数据表)

该表数据量最大，且包含大量的范围查询和多条件过滤。

### 查询模式分析：
- **按日期和时间范围过滤**：`WHERE date = %s AND time >= '09:25:00' AND time < '09:26:00'`
- **按股票代码精确匹配**：`WHERE code IN (%s, %s, ...)`
- **聚合查询 (MAX/MIN)**：`GROUP BY code` 配合 `MAX(time)` 或 `MIN(time)`。
- **关联查询 (Self-Join)**：通过 `(date, code, time)` 进行自关联以获取不同时刻的数据（如 9:15 与 9:25 的对比）。
- **排序**：按 `asking_amount` 或 `bidding_amount` 倒序。

### 推荐索引：
1. **复合覆盖索引 (最重要)**：
   ```sql
   CREATE INDEX idx_cad_date_time_code ON call_auction_data (date, time, code);
   ```
   *理由：绝大多数查询都以 `date` 为首要过滤条件，配合 `time` 的范围扫描，最后定位到 `code`。此索引能极大加速 `get_top_n_call_auction`、`get_ranking_by_time_range` 等核心方法。*

2. **代码优先的复合索引**：
   ```sql
   CREATE INDEX idx_cad_code_date_time ON call_auction_data (code, date, time);
   ```
   *理由：用于加速 `code IN (...)` 的查询，特别是当需要获取特定几只股票的历史时刻数据时。*

3. **数据量统计索引**：
   ```sql
   CREATE INDEX idx_cad_date_amount ON call_auction_data (date, bidding_amount DESC, bidding_percent);
   ```
   *理由：加速异动列表 (`get_abnormal_movement_at_925`) 和 TopN 列表的排序与过滤。*

---

## 2. 核心表：`yesterday_limit_up` (昨日涨停表)

该表通常存储前一交易日的统计数据，查询频率中等，但常与 `call_auction_data` 配合使用。

### 查询模式分析：
- **按日期和连板数过滤**：`WHERE date = %s AND consecutive_days >= 2`
- **按代码过滤**：`WHERE code IN (...)`

### 推荐索引：
1. **复合过滤索引**：
   ```sql
   CREATE INDEX idx_ylu_date_days ON yesterday_limit_up (date, consecutive_days, consecutive_boards);
   ```
2. **唯一标识索引**（如果尚未设置）：
   ```sql
   CREATE UNIQUE INDEX idx_ylu_date_code ON yesterday_limit_up (date, code);
   ```

---

## 3. 辅助统计表

### `market_sentiment_stats` (市场情绪统计)
- **推荐索引**：
  ```sql
  CREATE INDEX idx_mss_date_time ON market_sentiment_stats (date, time);
  ```

### `market_capacity` (市场容量/成交额)
- **推荐索引**：
  ```sql
  CREATE INDEX idx_mc_date ON market_capacity (date);
  ```

---

## 4. SQL 优化建议 (代码层面)

除了增加索引，建议在 `market_service.py` 中考虑以下改动：

1. **避免 `SELECT *`**：在 `get_yesterday_limit_up` 等方法中，明确指定需要的字段（如 `code, name, consecutive_days`），减少 I/O 负担。
2. **CTE 优化**：在 `get_abnormal_movement_at_925` 中，当前的子查询 `t_min_info` 可以改写为更高效的窗口函数（如果 MySQL 版本 >= 8.0），避免多次扫描表。
3. **冗余字段索引**：如果 `name LIKE '%ST%'` 过滤非常频繁，可以考虑增加一个布尔列 `is_st` 并建立索引，避免昂贵的字符串模糊匹配。

## 5. 执行计划验证
在应用索引后，建议针对以下方法生成的 SQL 执行 `EXPLAIN`：
- `get_top_n_call_auction`
- `get_abnormal_movement_at_925`
- `get_yesterday_limit_up_performance`

**预期效果**：查询应从 `ALL` (全表扫描) 或 `index` (全索引扫描) 变为 `range` 或 `ref`，显著降低 `rows` 扫描行数。
