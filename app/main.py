# 导入 FastAPI 和其他必要的库
from fastapi import FastAPI, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

# 从同级目录导入其他模块
# 注意：这些文件我们后续会逐步创建，这里先写好导入逻辑
from . import crud, models
from .database import engine, get_db
from .routers import novels, settings

# 创建数据库表
# 这行代码会根据你在 models.py 中定义的模型，在数据库中创建相应的表。
# 如果表已经存在，它不会重复创建。
models.Base.metadata.create_all(bind=engine)

# 初始化 FastAPI 应用实例
app = FastAPI(title="小说设定收录项目")

# 挂载静态文件目录
# 这使得 FastAPI 可以提供 CSS、JavaScript、图片等静态文件。
# '/static' 是 URL 路径, 'app/static' 是实际的文件夹路径。
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# 配置 Jinja2 模板
# 指定模板文件的存放目录。
templates = Jinja2Templates(directory="app/templates")

# 引入路由
# 将在 routers/novels.py 和 routers/settings.py 中定义的路由包含进来
# 这样做可以让主文件保持整洁，便于管理
app.include_router(novels.router)
app.include_router(settings.router)


# 定义根路由 (首页)
@app.get("/", summary="网站首页")
def read_root(request: Request, db: Session = Depends(get_db)):
    """
    处理访问网站根路径 ("/") 的请求。

    这个函数会:
    1. 从数据库获取所有小说。
    2. 使用 `index.html` 模板来渲染页面。
    3. 将小说列表数据传递给模板进行展示。
    """
    # 使用 crud 函数获取所有小说 (我们稍后会实现这个函数)
    all_novels = crud.get_novels(db=db)

    # 返回渲染后的 HTML 页面
    # "request": 模板渲染的必需参数
    # "novels": 传递给模板的数据
    return templates.TemplateResponse("index.html", {"request": request, "novels": all_novels})
