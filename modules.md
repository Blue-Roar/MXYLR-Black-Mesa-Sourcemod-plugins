# 模组

## 一、`bms_match` — 比赛插件(自研)

参考 hl2dm 的 xms 比赛插件、按 Black Mesa 引擎重写的比赛系统。
是 `BMAG.smx` 的一个模块,**不支持单独加载**。

### 玩家命令

| 命令 | 说明 |
|---|---|
| `!start` | 开始比赛。人数达到 `VoteMinPlayers` 时发起投票;否则(含 bot 时至少 2 人)直接开始 |
| `!cancel` | 取消比赛并恢复公服参数。比赛中需投票通过 |
| `!help` / `!commands` | 弹出比赛指令菜单(无线电菜单形式) |
| `!maplist` / `!list [模式]` | 查看地图池,`ffa` / `tdm` / `all`,默认当前模式 |
| `!run <地图>` / `!runnow <地图>` | 发起"换当前图"投票,支持 `模式:地图` 与缩写 |
| `!runnext <地图>` | 发起"设置下一张图"投票 |
| `!runrandom` | 从当前模式地图池随机抽 4 张发起换图投票 |
| `!shuffle` | 洗牌分队(仅 TDM) |
| `!invert` | 互换两队(仅 TDM) |
| `!yes` / `!no` / `!1`–`!5` | 投票表决 |
| `!pause` / `!unpause` | 暂停 / 继续服务器 |
| `!panel` / `!webpanel` | 打开游戏内网页控制台(见下) |
| `!vguitest` | 弹出测试用 VGUI 面板(比分板/隐藏变体,调试用) |

> `!pause` / `!unpause` 分两种情形:**比赛内**由 `bms_match` 自己接管(它直接发
> `ServerCommand("pause")` 并同步比赛状态机);**非比赛状态**下 `bms_match` 放行,由 SourceMod 核心
> 把 `!pause` 转成 `sm_pause` 交给 `pause` 模块(第三方插件 ddhoward `[Any?] Pause The Game`,
> 仍嵌在 `BMAG.smx` 内)。两者不要混用。

**聊天别名**:`!stop` → `!cancel`、`!join` → 加入人数较少的队伍、`!spec` → 观战、
`!next <图>` → `!runnext <图>`、`!random` → `!runrandom`。

`!run` 支持的地图缩写:`bunker`→`dm_lambdabunker`、`bounce`、`stalk`→`dm_stalkyard`、
`sub`→`dm_subtransit`、`gas`→`dm_gasworks`、`rail`、`crossfire`、`boom`。

### 管理员命令(需 b = 通用管理)

| 命令 | 说明 |
|---|---|
| `!forcespec <玩家>` | 强制某玩家转入观战 |
| `!allow <玩家>` | 放行某玩家加入比赛(解除开赛后的加入封锁) |
| `!starttest` | 启动一场 **1 分钟**的测试比赛,用于验证 SourceTV 录像链路 |

### ConVar

| ConVar | 默认 | 说明 |
|---|---|---|
| `sm_bms_webpanel_enabled` | 1 | 启用游戏内网页控制台(需要 socket 扩展)。**改这个会立即停/起监听** |
| `sm_bms_webpanel_url` | *(空)* | **面板对外的完整基址**,如 `https://panel.example.com`。走反代时设这个;留空则按下两行拼 `http://host:port` |
| `sm_bms_webpanel_bind` | `127.0.0.1` | 监听地址。有反代在前面时**保持回环**;留空 = `127.0.0.1`。**改动即时重绑** |
| `sm_bms_webpanel_host` | *(空)* | 仅当 `sm_bms_webpanel_url` 为空时使用:URL 里的 Host,留空 = `127.0.0.1` |
| `sm_bms_webpanel_port` | 28015 | 监听端口。**改动即时重绑**,不需要 reload 插件 |

> `_enabled` / `_bind` / `_port` 三个都挂了变更钩子:改完**立刻**拆掉旧监听并按新设置重新绑定,
> 下次地图加载时 `server.cfg` 里设的值也会自动生效。`_url` / `_host` 只是拼 URL 用的,每次请求现读,同样不用 reload。

### 命令监听(拦截引擎命令)

插件挂在这些引擎命令上,按比赛状态放行或吞掉:

| 命令 | 比赛中的行为 |
|---|---|
| `jointeam` / `spectate` / `chooseteam` | 开赛后封锁换边;经 `!allow` 放行 |
| `pause` / `unpause` / `setpause` | 暂停状态与比赛状态机同步;吞掉引擎自身的回显以免二次派发 |
| `kill` / `explode` | 倒计时与赛后结算阶段禁止自杀绕过冻结 |
| `changelevel` / `changelevel_next` | 比赛中阻止手动换图,由插件统一发起投票 |

### 比赛流程

1. `!start` → 人数 < `VoteMinPlayers` 直接开始,否则发起投票
2. 进入 MatchWait:执行 `exec server_match`(重置时限/封顶/复活)→ 冻结玩家并剥离武器 → 4 秒倒计时
3. 进入 Match:计时开始,锁定队伍;参赛者掉线自动暂停;FFA 取最高击杀(平局比死亡数),TDM 比队伍分
4. 平分 → 自动加时(Overtime,每分钟续时直到分出胜负)
5. 结束:广播胜利与比分 → `exec server_match_post` 恢复公服参数 → 自动发起下一张图投票 → 引擎自然换图

比赛自动开启 SourceTV 录像,文件落在服务器本机的 `demos\` 目录(不提供下载)。

**单人战役地图会被自动跳过**:判据是地图名前缀 `bm_c<数字>`(78 张战役图全部命中,与 DM 图无冲突)。
命中时跳过队伍枚举、静默 1Hz 定时器、并关闭 `fast_spawn`。

### 配置(`bms/addons/sourcemod/configs/bms_match.cfg`)

| 键 | 默认 | 说明 |
|---|---|---|
| `VoteMinPlayers` / `VoteMaxTime` / `VoteCooldown` | 3 / 25 / 30 | 投票人数门槛、时限、冷却(秒) |
| `AutoVoting` | 1 | 比赛结束自动发起下一图投票 |
| `DefaultMode` / `RetainModes` | ffa / ffa,tdm | 默认模式 / 换图后保留的模式 |
| `PreMatchCommand` / `PostMatchCommand` | `exec server_match` / `exec server_match_post` | 开赛 / 赛后执行的 cfg |
| `Gamemodes` | — | 每模式:`Command`(如 `mp_teamplay 0`)、`Mapcycle`、`Defaultmap`、`Matchable`、`Overtime`、`MatchTimelimit` |
| `Maps` | — | `StripPrefix`(显示时去掉的图名前缀)、`DefaultModes`(通配映射)、`Abbreviations`(图名缩写) |

地图池文件放在 `bms/cfg/` 下,由各模式的 `Mapcycle` 键引用。`ffa` 与 `tdm` 各 12 张官方 DM 图,
两份名单当前完全相同:
`dm_boom`、`dm_bounce`、`dm_chopper`、`dm_crossfire`、`dm_gasworks`、`dm_lambdabunker`、
`dm_power`、`dm_rail`、`dm_stack`、`dm_stalkyard`、`dm_subtransit`、`dm_undertow`。

---

## 二、其它自研 / 深度改造模块

以下 9 个模块都**编译在 `BMAG.smx` 内部**(见 [五、从源码构建](#五从源码构建)),不能单独加载。
`spawn_distribute`、`textmsg_fix` 为自研;其余基于 AlliedModders 社区插件,按本服需要做过适配或实质改造
(`fast_spawn`、`speclist` 源自 Alienmario,`SpecDetails` 源自 wribit,`missing_viewmodel_fix` 源自 ch4os + SHUFEN,
`advertisements` 源自 Tsunami;各文件头部保留原作者声明)。

| 模块 | 一句话 | 详见 |
|---|---|---|
| `fast_spawn` | 零秒重生,不等原生按键或 5 秒 `mp_forcerespawn` | 下节 |
| `spawn_distribute` | 复活点均匀分配,修原生同点堆人 | 下节 |
| `textmsg_fix` | CP936 下 UTF-8 中文消息导致的 `_vsnprintf` 崩溃 | 下节 |
| `adv-weapon_cleaner` | 掉落武器清扫 | 下节 |
| `SpecDetails` | 观察者详情 | 下节 |
| `speclist` | 观战者列表 | 下节 |
| `missing_viewmodel_fix` | 切队/切观察后重建 viewmodel | 下节 |
| `advertisements` | 轮播广告 | 下节 |
| `sm_noearbleed` | 去掉爆炸耳鸣/压耳声 | 下节 |

### `fast_spawn` — 零秒重生

死亡后立即重生,不等原生按键或 5 秒 `mp_forcerespawn`。

| 命令 | 权限 | 说明 |
|---|---|---|
| `fastspawn` / `sm_fs` | b | 查询或开关零秒重生 |

| ConVar | 默认 | 说明 |
|---|---|---|
| `sm_fastspawn` | 1 | 启用:死亡 `sm_fastspawn_time` 秒后重生 |
| `sm_fastspawn_batch` | 4 | 每个游戏 tick 最多重生几人(削平爆发重生;调小更平滑) |
| `sm_fastspawn_time` | 0.0 | 重生延迟秒数(0 = 立即) |

行为要点:

- 真人走 `OnPlayerRunCmd` 判定,`DispatchSpawn` 推迟到下一帧(避免在移动循环中途重入 `Spawn()` 导致"原地复活")
- bot 绕过 `OnPlayerRunCmd`,用 0.1 秒 timer 轮询模拟按键
- 致死伤害(`damage >= 血量`)时**先剥光武器再死**,避免掉落武器堆积;重生时给玩家加一帧 `FL_NOTARGET` 防止默认装备掉地上
- **单人战役地图与比赛期间自动关闭**(见 `bms_match` 一节):比赛期保留正常武器掉落,战役图避免误判高斯跳落地为致死

> 本服 `bms/cfg/server.cfg` 里显式设了 `sm_fastspawn 1` + `sm_fastspawn_time 0.0`(即最激进档)。

### `spawn_distribute` — 复活点均匀分配

BM 引擎原生的复活点选择链已损坏(`IsSpawnPointValid` 不读标旗、用零长度 trace 判定占用),
导致所有人被扔到同一个点。本模块不碰原生逻辑,在 `player_spawn` 事件里自己挑空闲点传送。

| ConVar | 默认 | 说明 |
|---|---|---|
| `spawn_distribute_enabled` | 1 | 开启(1 = 在 `player_spawn` 时挑空闲复活点传送) |
| `spawn_distribute_cooldown` | 2.0 | 同一点被分配后多少秒内不重复分配(0 = 关闭时间占用判定) |
| `spawn_distribute_radius` | 64.0 | 真人占用判定半径;范围内有**其他真人**即视为占用(bot 不参与) |

### `textmsg_fix` — 中文崩溃修复

修复 CP936 代码页下 UTF-8 中文消息尾字节悬空前导导致的 `_vsnprintf` fail-fast 崩溃。
无命令、无 ConVar,纯 Hook。

### `adv-weapon_cleaner` — 掉落武器清扫

| ConVar | 默认 | 说明 |
|---|---|---|
| `adv_weapon_cleaner_keep_map_weapons` | 1 | 是否保留地图固有武器(0 = 清,1 = 留) |
| `adv_weapon_cleaner_much_weapons` | 100 | 触发清理的武器数阈值(含玩家背包) |
| `adv_weapon_cleaner_remove_delay` | 20.0 | 玩家丢下武器后等待多久移除 |
| `adv_weapon_cleaner_remove_delay2` | 0.1 | 每把武器的递减延迟 |
| `adv_weapon_cleaner_sweep_interval` | 10.0 | 全量清扫间隔秒数(0 = 关闭清扫) |
| `adv_weapon_cleaner_version` | 1.0 | 版本号 |

只跟踪 `weapon_*`,不误删 `item_*`(充电器、道具)。判定依据是 `m_bRemoveable` 数据表字段。

### `SpecDetails` — 观察者详情

| ConVar | 默认 | 说明 |
|---|---|---|
| `sm_specDetails_enabled` | 1 | 启用/关闭本插件 |

比赛期间自动禁用(避免面板风暴;面板更新有 5 秒冷却)。

### `speclist` — 观战者列表

无命令、无 ConVar。定时刷新观战者名单显示。

### `missing_viewmodel_fix` — 缺失持枪模型修复

无命令、无 ConVar。挂 `jointeam` 与 `client_specmode` 监听,在切换队伍/观察模式后重建 viewmodel。
参考来源存档在 `smx_analysis/mvf_wb.html`(AlliedModders 原帖)。

### `advertisements` — 轮播广告

| 命令 | 权限 | 说明 |
|---|---|---|
| `sm_advertisements_reload` | b | 重新读取广告文件 |

| ConVar | 默认 | 说明 |
|---|---|---|
| `sm_advertisements_enabled` | 1 | 启用/关闭广告显示 |
| `sm_advertisements_file` | advertisements.txt | 广告文本文件 |
| `sm_advertisements_interval` | 30 | 广告间隔秒数 |
| `sm_advertisements_random` | 0 | 随机顺序播放 |

> 本服 `bms/cfg/server.cfg` 里把 `sm_advertisements_interval` 改成了 **600**(10 分钟一条),
> 不是上面表里的插件默认值 30。

### `sm_noearbleed` — 去除耳鸣/压耳声

无命令,仅 `sm_noearbleed_version`。挂 `OnTakeDamage` 把 `DMG_BLAST` 改成 `DMG_GENERIC` 以去掉爆炸耳鸣效果(不改伤害数值)。
来源:GitHub `foobarhl/sourcemod` —— 第三方社区插件,**不是 SourceMod 官方插件**,上游官方包里没有对应源码。

---

## 三、官方插件:全部交给用户自己装

### 设计原则

相较于上游仓库，此修改版的 **`BMAG.smx` 里不包含任何一个 SourceMod 官方插件** 。
官方插件(admin-flatfile、adminmenu、adminhelp、basechat、basecomm、basecommands、
basevotes、funcommands、playercommands、rockthevote、mapchooser、clientprefs、antiflood、
sounds、reservedslots、sql-admin-manager、admin-sql-*、nominations、randomcycle、basebans …)
**由用户自己的 SourceMod 安装提供**，本仓库不再重复打包。

这样做的好处是**部署零冲突**:把 `BMAG.smx` 丢进一个**原始的 SourceMod 安装**(官方插件该开的开着、
该在 `plugins/disabled/` 的放着),不会出现同名命令被两边注册、admin 菜单分类重名之类的撞车,
**不需要停用任何官方插件**。

BMAG 只负责 SourceMod 不自带的那部分:自研模块([一](#一bms_match--比赛插件自研)、[二](#二其它自研--深度改造模块))
与第三方插件(下表)。

### 编在 `BMAG.smx` 里、且官方包没有的(6 个)

| 模块 | 作用 | 备注 |
|---|---|---|
| `admincheats` | `sm_admin_cheats_level` 控制执行作弊命令所需权限 | 社区插件(devicenull),官方包不含 |
| `connectmessage` | 玩家加入/离开时聊天框提示 | 社区插件 |
| `motd-fixer` | 延时打开 MOTD(引擎自带 MOTD 触发有时序问题) | 社区插件;用 `clientprefs.ext` 的 cookie 记偏好 |
| `pause` | 暂停/继续服务器(`sm_pause` / `sm_unpause` / `sm_setpause`) | **第三方插件**(ddhoward `[Any?] Pause The Game` 18.0114.0)。它只注册 `sm_*` 命令并挂引擎 `pause` 命令监听;聊天里的 `!pause` 由 **SourceMod 核心**把 `!x` 转成 `sm_x` 触发,不依赖 `basechat`。比赛内 `!pause` / `!unpause` 由 `bms_match` 接管,两者不要混用 |
| `showhealth` | 屏幕上显示血量(`sm_show_health` / `sm_show_health_on_hit_only` / `sm_show_health_text_area`) | **第三方插件**;用 `clientprefs.ext` 的 cookie 记"关掉血量显示"的偏好 |
| `teamjoinblocker` | 换边封锁(`sm_toggle_join` / `sm_a`) | 社区插件 |

### 交给用户自己装的官方插件(19 个)

以下模块原本嵌在 `BMAG.smx` 里,**现已全部移出**;它们的源码也**已从本仓库删除**
(想重新合并的话见本节末尾的注意事项)。

「官方包状态」一列指 SourceMod 官方压缩包里 `addons/sourcemod/plugins/` 的默认位置 ——
**`plugins/` = 装完就启用**;**`plugins/disabled/` = 装完是停用的,要用得自己挪出来**。

| 模块 | 提供什么 | 官方包状态 |
|---|---|---|
| `admin-flatfile` | 从管理员名单读管理员 —— **仓库里那份配置就是给它用的,必须启用它才有管理员** | `plugins/` |
| `adminhelp` | `sm_help` / `sm_searchcmd` | `plugins/` |
| `adminmenu` | `sm_admin` 管理员菜单 | `plugins/` |
| `antiflood` | 聊天刷屏限制(`sm_flood_time`) | `plugins/` |
| `basechat` | `sm_say` / `sm_csay` / `sm_hsay` / `sm_msay` / `sm_tsay` / `sm_chat` / `sm_psay`(`bms/cfg/server.cfg` 第 58 / 85 / 99 行用到 `sm_say`) | `plugins/` |
| `basecomm` | 禁言/禁麦(`sm_gag` / `sm_mute` / `sm_silence` 及解除) | `plugins/` |
| `basecommands` | `sm_kick` / `sm_map` / `sm_cvar` / `sm_rcon` / `sm_execcfg` / `sm_cancelvote` / `sm_who` / `sm_reloadadmins` | `plugins/` |
| `basetriggers` | 聊天触发词(`timeleft` / `nextmap` / `motd` / `ff`) | `plugins/` |
| `basevotes` | `sm_vote` / `sm_voteban` / `sm_votekick` / `sm_votemap` | `plugins/` |
| `clientprefs` | 客户端 cookie 界面(`sm_cookies` / `sm_settings`) | `plugins/` |
| `funcommands` | 娱乐命令(`sm_beacon` / `sm_blind` / `sm_burn` / `sm_drug` / `sm_freeze` / `sm_gravity` / `sm_noclip` 等) | `plugins/` |
| `funvotes` | 娱乐投票(`sm_votealltalk` / `sm_voteburn` / `sm_voteff` / `sm_votegravity` / `sm_voteslay`) | `plugins/` |
| `playercommands` | `sm_slap` / `sm_slay` / `sm_rename` | `plugins/` |
| `reservedslots` | 预留通道(`sm_reserve_*` / `sm_hide_slots`) | `plugins/` |
| `sounds` | `sm_play` 播放声音 | `plugins/` |
| `mapchooser` | 结束换图投票、`sm_setnextmap` / `sm_mapvote`、`EndOfMapVoteEnabled()` 等 native | ⚠️ `plugins/disabled/` |
| `nominations` | 地图提名(`sm_nominate`) | ⚠️ `plugins/disabled/` |
| `rockthevote` | RTV 换图(`sm_rtv`) | ⚠️ `plugins/disabled/` |
| `sql-admin-manager` | SQL 管理员增删改(`sm_sql_*`) | ⚠️ `plugins/disabled/` |

> **只影响一个地方**:`advertisements` 会调 `EndOfMapVoteEnabled()` / `HasEndOfMapVoteFinished()`
> 来避开结束换图投票。这两个 native 由 **`mapchooser.smx`** 提供,而它在官方包里默认停用 ——
> 所以 `BMAG.smx` 把这条插件依赖做成了**软依赖**(见下),没启用 mapchooser 也能正常加载,
> 只是 `advertisements` 的那段检查会被跳过。想让结束换图投票真正生效就把 `mapchooser.smx` 挪出来。

### `BMAG.smx` 的依赖形态

移出这 19 个之后,BMAG 对**插件**的依赖只剩一条,而且是软的:

| 依赖 | 类型 | 说明 |
|---|---|---|
| clientprefs.ext / geoip.ext / sdktools.ext / sdkhooks.ext | 扩展,硬依赖 | SourceMod 官方包自带(1.12 已核对) |
| socket.ext | 扩展,**硬依赖** | ⚠️ **官方包不含**,必须随本仓库分发 |
| `mapchooser` | 插件库,**软依赖**(`required = 0`) | `merge.py` 在 `#include <mapchooser>` 前 `#undef REQUIRE_PLUGIN`,使 `SharedPlugin` 块编译成 `required = 0` 并让 include 生成 `__pl_mapchooser_SetNTVOptional()`,把 9 个 mapchooser native 全部标记为可选 |

核对方式(可复现):解压 `BMAG.smx` 的 section 后,`adminmenu` / `basecomm` / `topmenus`
的引用数为 **0**,`__pl_mapchooser` 结构体里的 `required` 字段是 `0`,
`GetAdminTopMenu` / `AddTargetsToMenu` / `BaseComm_*` 全部不再被引用。

---

## 四、独立插件

> **单人战役插件 `tau_mp` / `hl1tau` 已移出本仓库**，需要请前往上游仓库获取。
> 原先随它们一起的签名文件 `tau_mp.games.txt` 与逆向笔记 `REVERSE_TAU.md` 也一并移出。

### `spawn_marker.smx` — 复活点标记(**默认停用**)

训练用工具:在 `player_spawn` 时标记真实落点。

| 命令 | 权限 | 说明 |
|---|---|---|
| `sm_spawnmarker` | b | 开关复活点标记 |
| `sm_spawnmap` | b | 开关全图复活点常显 |
| `sm_sm` | b | 快捷别名 |

| ConVar | 默认 | 说明 |
|---|---|---|
| `sm_spawnmarker_enabled` | 0 | 启用敌方复活点标记(0 = 关) |
| `sm_spawnmarker_life` | 5.0 | 标记存在时长(秒) |
| `sm_spawnmarker_spawnmap` | 0 | 持续显示所有死亡竞赛复活点 |

### 第三方插件(无源码)

| 插件 | 作用 |
|---|---|
| `bms_rpgReloadFix.smx` | RPG 换弹动画修复 |
| `bms_weapon_tauStuckFix.smx` | tau 低弹药卡枪修复:右键按下第一 tick 且手持 `weapon_tau` 时把备用弹药补到 3 |
| `is_weaponfx.smx` | 武器动画预热:玩家入服后假连 `is_weaponfix_saddr` 预缓存动画再重连(需在 `server.cfg` 显式设该地址,默认值会被视为"未配置"而自我禁用) |
| `is_bms_fix_timelimit.smx` | 回合时限/倒计时修复(BM 只在地图加载时读一次 `mp_timelimit`,运行期 `SetInt` 无效;它走 `mp_round_time` 实体的加时输入 —— `bms_match` 的计时器沿用同一机制) |
