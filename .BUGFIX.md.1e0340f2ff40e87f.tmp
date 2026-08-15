## Bug 修复记录

### v0.1.1 - 角色无法移动 (2026-08-15)

**问题描述：** 游戏开始后，点击方向键角色完全不移动。

**排查过程：**
1. ✅ init() 在脚本底部正确调用
2. ✅ onclick="move(0,-1)" 等事件绑定正确
3. ✅ keydown 监听器正确注册
4. ✅ startGame() 后 state 正确设为 EXPLORE
5. ❌ **canvas 元素遮挡了 controls**

**根本原因：**
- canvas 在 DOM 中排在 controls 之前
- canvas 没有设置 z-index（默认 auto）
- controls 设置了 z-index: 5
- 但浏览器渲染顺序：先渲染的元素默认堆叠在上层
- 结果：canvas 覆盖在整个 controls 上方，触摸完全无效

**修复方案：**
```css
canvas {
    z-index: 1;  /* 新增：确保低于 controls */
}
#controls {
    z-index: 5;  /* 保持不变 */
}
```

**验证：**
- 触摸按钮现在可以正常触发 move()
- 键盘方向键正常工作
- OK 按钮正常工作
- 控制台有 [DEBUG] 日志便于后续排查
