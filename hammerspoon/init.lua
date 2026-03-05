local function moveWindowToLeft()
    local win = hs.window.focusedWindow()
    local screen = win:screen():frame()
    win:setFrame({ x = screen.x, y = screen.y, w = screen.w / 2, h = screen.h })
end

local function moveWindowToRight()
    local win = hs.window.focusedWindow()
    local screen = win:screen():frame()
    win:setFrame({ x = screen.x + screen.w / 2, y = screen.y, w = screen.w / 2, h = screen.h })
end

local hyper = { "ctrl", "cmd", "alt", "shift" }

hs.hotkey.bind(hyper, "h", moveWindowToLeft)
hs.hotkey.bind(hyper, "l", moveWindowToRight)
hs.hotkey.bind(hyper, "k", function()
    hs.window.focusedWindow():maximize()
end)
