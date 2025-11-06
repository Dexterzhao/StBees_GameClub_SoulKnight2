# Pygame Client Framework (Demo)

这是一个最小的 pygame 单机客户端框架，包含登录界面、主菜单、继续/查看存档和退出功能。游戏逻辑为占位实现，便于后续扩展。

依赖

- Python 3.8+
- pygame

安装与运行

```bash
python -m pip install -r requirements.txt
python main.py
```

快捷键

- Enter: 在登录界面继续
- S: 在游戏场景中保存
- Esc: 从游戏或存档返回主菜单

存档

存档以 JSON 文件保存在 `saves/` 目录（程序第一次运行会创建）。

后续可以在 `scenes/game.py` 中实现具体游戏玩法，并通过 `save_manager.py` 持久化游戏状态。
