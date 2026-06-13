# TQ 电表 — Home Assistant 自定义集成

将 TQ 电表（拓强电表 `app.tqdianbiao.com`）的数据接入 Home Assistant。

## 功能

- 电费余额
- 累计用电量
- 昨日用电量
- 抄表时间
- 最近充值金额和日期
- 电表类型
- 手动刷新抄表

## 安装

### 通过 HACS

1. 打开 HACS → 自定义仓库 → 添加本仓库 URL
2. 搜索「TQ 电表」并安装
3. 重启 HA
4. 设置 → 集成 → 添加集成 → 搜索「TQ 电表」

### 手动安装

```bash
cd /config/custom_components
git clone https://github.com/your/ha-tqdianbiao.git tqdianbiao
```

重启 HA 后添加集成。

## 配置

需要输入 TQ 电表 App 的登录手机号、密码，以及自定义设备名称。

## 实体

| 实体 | 类型 | 说明 |
|---|---|---|
| `sensor.tqdianbiao_balance` | sensor | 电费余额（元） |
| `sensor.tqdianbiao_total_usage` | sensor | 累计用电量（kWh） |
| `sensor.tqdianbiao_yesterday_usage` | sensor | 昨日用电量（kWh） |
| `sensor.tqdianbiao_update_time` | sensor | 抄表时间 |
| `sensor.tqdianbiao_latest_pay_amount` | sensor | 最近充值金额（元） |
| `sensor.tqdianbiao_latest_pay_date` | sensor | 最近充值日期 |
| `sensor.tqdianbiao_meter_type` | sensor | 电表类型 |
| `button.tqdianbiao_refresh` | button | 刷新抄表 |

## 数据更新

每 30 分钟自动轮询一次。也可点击「刷新抄表」按钮立即获取最新数据（1 分钟限 1 次）。
