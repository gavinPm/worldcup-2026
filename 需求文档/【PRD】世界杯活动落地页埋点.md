# 【PRD】世界杯活动落地页埋点

## 文档信息

<!-- col_widths=[120, 290, 120, 290] -->
| 产品名称 |  | **文档编号** |  |
|---|---|---|---|
| 所属系统 | 世界杯活动 | **文档版本** | V-1.0.0 |
| 撰写人 |  | **编写日期** | 2026-05-14 |

## 修订记录

<!-- header_row=True col_widths=[100, 100, 100, 420, 100] -->
| 版本号 | 日期 | 类型 | 描述 | 撰写人 |
|---|---|---|---|---|
| V-1.0.0 | 2026-05-14 | 新增 | 初稿 |  |

## 关联文档

<!-- header_row=True col_widths=[150, 400, 270] -->
| 类型 | 链接 | 说明 |
|---|---|---|
| 页面 PRD | 需求文档/【PRD】世界杯活动落地页.md |  |
| 上报接口 | 埋点上报接口设计文档 |  |

## 需求描述

1. 本文档覆盖世界杯活动落地页的埋点需求
1. 页面所有关键交互行为均需上报
1. 上报接口定义详见《埋点上报接口设计文档》

---

## 公共上报字段

每次事件上报均需携带以下公共字段：

<!-- header_row=True col_widths=[180, 80, 80, 480] -->
| 接口字段 | 类型 | 是否必传 | 说明 |
|---|---|---|---|
| eventType | string | 是 | 事件类型（一级分类），取值见各事件定义 |
| eventName | string | 是 | 事件名称（二级分类），取值见各事件定义 |
| platform | string | 是 | 客户端类型：PC / IOS / ANDROID / H5 |
| device.os | string | 否 | 设备系统，如 iOS、Android |
| device.osVersion | string | 否 | 设备系统版本 |
| device.module | string | 否 | 设备型号 |
| device.deviceId | string | 否 | 设备标识 |
| appVersion | string | 否 | 客户端版本号 |
| networkType | string | 否 | 网络类型：wifi / 4g / 5g / unknown |
| eventTimestamp | long | 是 | 事件发生时间，毫秒级时间戳 |
| pageUrl | string | 是 | 当前页面完整 URL |
| requestUrl | string | 否 | 触发事件时调用的后端接口 URL |
| currentBaseUrl | string | 否 | 当前使用的线路地址 |
| language | string | 是 | 用户客户端语言，如 zh-TW、en |
| eventDetail | object | 是 | 事件详情，各事件自定义字段，见各节说明 |
| ext.uuid | string | 否 | 用户 UUID，已登录时传入，未登录不传或传空 |
| message | string | 否 | 描述信息，不传时由服务端用 eventType+eventName 拼接 |

---

## 世界杯活动落地页

**页面 URL 规则**：`https://www.bittap.com/{语言}/activity/worldcup-2026`

---

### 1. 页面 & Banner

<!-- header_row=True col_widths=[160, 200, 100, 280, 280] -->
| 埋点事件 | 触发时机 | eventType | eventName | eventDetail |
|---|---|---|---|---|
| 页面浏览 | 页面渲染完成时 | view | worldcup_view | activity_id |
| 点击语言切换 | 用户点击语言切换按钮 | click | worldcup_lang_switch_click | activity_id |
| 选择语言 | 用户在弹窗中点击某语言确认 | click | worldcup_lang_select | activity_id、lang |
| 点击分享 | 用户点击 Banner 分享按钮 | click | worldcup_share_click | activity_id、login_status |
| 分享弹窗操作 | 用户在分享弹窗内点击操作按钮 | click | worldcup_share_action | activity_id、btn_name |
| 点击我的奖品 | 用户点击「我的奖品」按钮 | click | worldcup_my_reward_click | activity_id |
| 点击 Banner 获取更多世界币 | 用户点击 Banner 区「获取更多世界币」按钮 | click | worldcup_banner_get_coin_click | activity_id |
| 点击活动规则（Banner） | 用户点击 Banner 区「活动规则」按钮 | click | worldcup_banner_rule_click | activity_id |

**eventDetail 字段说明**

<!-- header_row=True col_widths=[160, 80, 580] -->
| 字段名 | 类型 | 说明 |
|---|---|---|
| activity_id | string | 活动 ID |
| lang | string | 用户选择的语言，如 zh、en、ja |
| login_status | bool | true = 已登录；false = 未登录 |
| btn_name | string | 操作按钮标识：save_image（保存图片）/ copy_link（复制链接）/ twitter / telegram |

---

### 2. Tab 导航

<!-- header_row=True col_widths=[160, 200, 100, 280, 280] -->
| 埋点事件 | 触发时机 | eventType | eventName | eventDetail |
|---|---|---|---|---|
| 点击 Tab | 用户点击任意 Tab 项 | click | worldcup_tab_click | activity_id、tab_name |

**eventDetail 字段说明**

<!-- header_row=True col_widths=[160, 80, 580] -->
| 字段名 | 类型 | 说明 |
|---|---|---|
| activity_id | string | 活动 ID |
| tab_name | string | match（每日竞猜）/ lottery（抽奖）/ get_coin（获取更多世界币）/ leaderboard（排行榜）/ coin_record（世界币记录） |

---

### 3. 每日竞猜

<!-- header_row=True col_widths=[160, 200, 100, 280, 280] -->
| 埋点事件 | 触发时机 | eventType | eventName | eventDetail |
|---|---|---|---|---|
| 点击竞猜卡片 | 用户点击预测市场竞猜卡片，跳转至预测市场事件详情页 | click | worldcup_predict_card_click | activity_id、predict_id |
| 点击查看更多 | 用户点击竞猜区「查看更多」按钮，跳转至预测市场业务主页 | click | worldcup_predict_more_click | activity_id |

**eventDetail 字段说明**

<!-- header_row=True col_widths=[160, 80, 580] -->
| 字段名 | 类型 | 说明 |
|---|---|---|
| activity_id | string | 活动 ID |
| predict_id | string | 预测市场事件 ID |

---

### 4. 抽奖

<!-- header_row=True col_widths=[160, 200, 100, 280, 280] -->
| 埋点事件 | 触发时机 | eventType | eventName | eventDetail |
|---|---|---|---|---|
| 点击抽奖 | 用户点击抽奖按钮（余额和次数均满足时） | click | worldcup_lottery_click | activity_id |
| 抽奖结果 | 走马灯动效结束，结果展示时 | submit | worldcup_lottery_result | activity_id、prize_type、prize_amount、prize_currency |

**eventDetail 字段说明**

<!-- header_row=True col_widths=[160, 80, 580] -->
| 字段名 | 类型 | 说明 |
|---|---|---|
| activity_id | string | 活动 ID |
| prize_type | string | 奖品类型：crypto（加密货币）/ voucher（代金券）/ world_coin（世界币） |
| prize_amount | string | 奖品数量 |
| prize_currency | string | 奖品币种 / 券名称，如 BTC、USDT、体验金券 |

---

### 5. 获取世界币

#### 5.1 签到

<!-- header_row=True col_widths=[160, 200, 100, 280, 280] -->
| 埋点事件 | 触发时机 | eventType | eventName | eventDetail |
|---|---|---|---|---|
| 点击签到 | 用户点击当日高亮签到格 | click | worldcup_checkin_click | activity_id、checkin_day |
| 签到成功 | 签到接口返回成功后 | submit | worldcup_checkin_success | activity_id、checkin_day、reward_amount |

**eventDetail 字段说明**

<!-- header_row=True col_widths=[160, 80, 580] -->
| 字段名 | 类型 | 说明 |
|---|---|---|
| activity_id | string | 活动 ID |
| checkin_day | int | 本次签到为连签第几天，1–10 |
| reward_amount | int | 本次签到发放世界币数量 |

#### 5.2 社交任务

<!-- header_row=True col_widths=[160, 200, 100, 280, 280] -->
| 埋点事件 | 触发时机 | eventType | eventName | eventDetail |
|---|---|---|---|---|
| 点击任务入口 | 用户点击「立即关注 / 立即评论 / 立即加入」 | click | worldcup_social_task_start | activity_id、task_type |
| 点击确认完成 | 用户点击「我已关注 / 我已评论 / 我已加入」 | click | worldcup_social_task_confirm | activity_id、task_type |
| 社交任务完成 | 确认接口返回成功后 | submit | worldcup_social_task_success | activity_id、task_type |

**eventDetail 字段说明**

<!-- header_row=True col_widths=[160, 80, 580] -->
| 字段名 | 类型 | 说明 |
|---|---|---|
| activity_id | string | 活动 ID |
| task_type | string | follow_x（关注X）/ comment_x（评论X帖子）/ follow_tg（关注Telegram） |

#### 5.3 合约任务

<!-- header_row=True col_widths=[160, 200, 100, 280, 280] -->
| 埋点事件 | 触发时机 | eventType | eventName | eventDetail |
|---|---|---|---|---|
| 点击立即交易 | 用户点击合约任务卡片右上角「立即交易」 | click | worldcup_contract_trade_click | activity_id |

---

### 6. 排行榜

<!-- header_row=True col_widths=[160, 200, 100, 280, 280] -->
| 埋点事件 | 触发时机 | eventType | eventName | eventDetail |
|---|---|---|---|---|
| 排行榜翻页 | 用户点击排行榜分页控件 | click | worldcup_leaderboard_page | activity_id、page_num |

**eventDetail 字段说明**

<!-- header_row=True col_widths=[160, 80, 580] -->
| 字段名 | 类型 | 说明 |
|---|---|---|
| activity_id | string | 活动 ID |
| page_num | int | 翻页后当前页码，从 1 开始 |

---

### 7. 世界币记录

<!-- header_row=True col_widths=[160, 200, 100, 280, 280] -->
| 埋点事件 | 触发时机 | eventType | eventName | eventDetail |
|---|---|---|---|---|
| 世界币记录翻页 | 用户点击世界币记录分页控件 | click | worldcup_coin_record_page | activity_id、page_num |

**eventDetail 字段说明**

<!-- header_row=True col_widths=[160, 80, 580] -->
| 字段名 | 类型 | 说明 |
|---|---|---|
| activity_id | string | 活动 ID |
| page_num | int | 翻页后当前页码，从 1 开始 |

---

### 8. 活动规则

<!-- header_row=True col_widths=[160, 200, 100, 280, 280] -->
| 埋点事件 | 触发时机 | eventType | eventName | eventDetail |
|---|---|---|---|---|
| 展开 / 收起 FAQ | 用户点击 FAQ 标题行 | click | worldcup_faq_toggle | activity_id、faq_index、is_expand |

**eventDetail 字段说明**

<!-- header_row=True col_widths=[160, 80, 580] -->
| 字段名 | 类型 | 说明 |
|---|---|---|
| activity_id | string | 活动 ID |
| faq_index | int | FAQ 条目序号，从 1 开始 |
| is_expand | bool | true = 展开；false = 收起 |
