# Fold Studio · 立体展开设计台

输入长、宽、高，生成长方体的 3D 线框模型和带尺寸标注的十字展开图。支持鼠标旋转、缩放、连续折叠动画、SVG 导出，以及方案保存、加载和删除。

## 技术与目录

- `frontend/`：Vue 3 + TypeScript + Vite + Three.js。直接通过 HTTP 调用后端，无服务端模板。
- `backend/`：Python 3.12 + FastAPI + SQLAlchemy + PyMySQL。后端计算几何与 SVG，数据保存至真实 MySQL。
- `scripts/`：Windows 安装、启动、停止及 HTTP 联调脚本。
- `.runtime/`：项目私有 MySQL 8.4.11 LTS、数据目录、日志和凭据。已加入 Git 忽略。

## 本机启动

将仓库克隆到任意本地目录后，在项目根目录（包含 `README.md`、`scripts/`、`frontend/` 和 `backend/` 的目录）打开 PowerShell。以下安装、启动和停止命令均在项目根目录执行；脚本会自动定位项目路径，无需固定盘符或目录名。

首次运行需要 Node.js 22.12+、Python 3.10+、网络和 MySQL 所需的 Microsoft Visual C++ 运行库。先安装依赖并初始化数据库，安装完成后会自动启动项目：

```powershell
.\scripts\install.ps1 -Python 'python'
```

后续启动：

```powershell
.\scripts\start.ps1
```

- 页面：http://127.0.0.1:5173
- API 文档：http://127.0.0.1:8000/docs
- 健康检查：http://127.0.0.1:8000/api/health
- MySQL：`127.0.0.1:3307`，数据库 `fold_studio`，应用账号 `fold_app`

脚本下载官方 MySQL ZIP，在项目内初始化实例；无需 Docker 或注册 Windows 服务。安装时生成随机密码，应用连接串写入 `backend/.env`，管理凭据写入 `.runtime/mysql-credentials.json`，不要提交或公开这两个文件。数据库只监听本机回环地址；初始化空密码状态仅用于首次创建随机密码，初始化失败时请停止实例并检查日志后重试。

停止（保留数据库）：

```powershell
.\scripts\stop.ps1
```

启动脚本在后台运行三个进程，并在 `.runtime/` 保存日志和进程编号。端口被其他程序占用时，请先处理冲突。数据库数据保存在 `.runtime/mysql-data/`，不要删除；备份前使用 MySQL 备份工具，或正常停止后复制数据目录。

## 前后端独立运行

先启动 MySQL，可先运行整体启动脚本。然后在需要独立调试时使用：

```powershell
# 后端（backend 目录）
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
# 前端（frontend 目录，另开终端）
npm.cmd run dev
```

独立调试前停止对应的既有进程，避免占用相同端口。前端通过 `VITE_API_BASE_URL` 配置后端地址，示例见 `frontend/.env.example`；后端通过 `DATABASE_URL` 与 `CORS_ORIGINS` 配置数据库和允许来源。改动前端环境变量需重新启动 Vite。

## API

| 方法 | 路径 | 功能 |
| --- | --- | --- |
| GET | `/api/health` | 实际检查 MySQL 连接 |
| POST | `/api/geometry` | 输入 `{ "length": 240, "width": 160, "height": 100 }`，返回六面坐标、折线、面积和体积 |
| POST | `/api/export/svg` | 相同尺寸输入，返回 SVG 文件 |
| GET | `/api/designs` | 最近 100 条保存方案 |
| POST | `/api/designs` | 尺寸加 `name` 保存方案 |
| DELETE | `/api/designs/{id}` | 删除方案 |

尺寸范围 1–10000 mm，支持小数；页面面积使用 cm²、体积使用 cm³。当前几何为理想长方体，未计入材料厚度、粘贴边、出血或实际制造公差。极端长宽比下小面和文字会难以辨识，可导出矢量图放大查看。仅面向本地单用户使用，未实现账号系统。

## 验证

```powershell
# 项目根目录
npm.cmd run build --prefix frontend
.\.venv\Scripts\python.exe -m pytest -q
# 服务启动后验证真实 HTTP 与 MySQL
.\.venv\Scripts\python.exe scripts\smoke_test.py
```

几何测试检查六面面积、体积、展开图边界、面之间不重叠、非法尺寸和 SVG 格式；联调脚本检查数据库健康、校验、CORS、导出、保存、读取和删除，并清理测试记录。

## 垫块 / 垫点
在预览下方点击添加垫块，可设置名称、长宽高及 X/Y/Z 坐标，支持最多 100 个。原点为箱体底面中心，位置为垫块底面中心；X 向右、Y 向上、Z 向前，单位 mm。允许负坐标、箱外、悬空和相互重叠，不自动吸附或碰撞限制。点击模型或列表选择，使用定位垫块聚焦远处对象。展开时垫块保持空间位置，平面展开和 SVG 包含垫块在底面坐标系的投影、编号、尺寸和底部高度。保存方案时包含全部垫块，旧方案自动显示为空列表。已有安装升级前可运行 .venv/Scripts/python.exe scripts/migrate_pads.py 创建关联表；新安装自动建表。
垫块 HTTP 联调：.venv/Scripts/python.exe scripts/smoke_pads.py


## 尺寸与边距标注
立体预览显示箱体长宽高尺寸线，选中垫块时显示其长宽高与左、右、前、后、底、顶六向边距。边距从垫块外缘到闭合箱体对应面计算，负值表示该方向越界。展开过程中保留闭合尺寸数据，隐藏空间尺寸线。平面图中垫块为底面投影，并非将悬空垫块贴在底面；高度由图例说明。外部垫块自动纳入图幅。

## 板材厚度
箱体设置支持板厚（0–1000 mm，且严格小于最短边的一半），默认 0 兼容旧方案。长宽高为外尺寸，内腔各尺寸减去两倍板厚；垫块不含板厚参数，边距计算到板材内表面。Y 坐标仍相对箱体外底面，新垫块默认 Y=板厚。三维为六块等厚面板示意，角部不作拼接裁切处理；平面图仍为外表面展开示意，SVG 标出板厚，不用于直接制造下料。旧安装升级运行 scripts/migrate_thickness.py。


## 展开补偿
板厚大于 0 时，展开图自动计算接缝边与 90° 折弯补偿：内弯半径按板厚估算，中性层 K=0.5；折弯补偿为 π/2 × (R + K×T)，接缝边为 max(3T, 5mm)。补偿只作用于平面下料图，3D 外形尺寸保持输入值。图中以橙色虚线表示补偿边，并显示 seam / bend 参数。实际制造前应按材料、刀具和折弯工艺校准 K 值。
