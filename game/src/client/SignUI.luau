-- Writing on a sign. Opened when the owner presses F on one; what is typed is sent to the server,
-- which filters it before anyone sees it on the sign.
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Net = require(Shared:WaitForChild("Net"))
local SocialLogic = require(Shared:WaitForChild("SocialLogic"))
local Screens = require(script.Parent.Screens)
local UIKit = require(script.Parent.UIKit)

local SignUI = {}

type Target = { owner: number, x: number, y: number, z: number }

local box: TextBox
local counter: TextLabel
local target: Target? = nil

local function count()
	local cleaned = SocialLogic.cleanSign(box.Text)
	local length = if cleaned then utf8.len(cleaned) else nil
	local typed = utf8.len(box.Text)
	-- Typed more than fits: say so, since the rest will be cut.
	local over = cleaned == nil or (typed ~= nil and length ~= nil and typed > length + 8)
	counter.Text = (if length then tostring(length) else "?") .. " / " .. SocialLogic.SIGN_CHARS .. "자"
	counter.TextColor3 = if over then UIKit.BAD else UIKit.DIM
end

local function send(text: string)
	local at = target
	if at then
		Net.get("MachineAct"):FireServer(at.owner, at.x, at.y, at.z, "write", text)
	end
	Screens.close("sign")
end

local function onInfo(message: any)
	if type(message) ~= "table" or message.kind ~= "sign" or type(message.info) ~= "table" then
		return
	end
	if type(message.owner) ~= "number" or type(message.x) ~= "number" then
		return
	end
	target = { owner = message.owner, x = message.x, y = message.y, z = message.z }
	box.Text = if type(message.info.text) == "string" then message.info.text else ""
	count()
	Screens.open("sign")
	box:CaptureFocus()
end

function SignUI.init(_hotbar)
	local _, body = UIKit.window("sign", "표지판에 글 쓰기", 460, 270, nil, nil, function()
		target = nil
	end)

	box = UIKit.input(body, "여기에 적으세요", 16)
	box.MultiLine = true
	box.TextWrapped = true
	box.TextXAlignment = Enum.TextXAlignment.Left
	box.TextYAlignment = Enum.TextYAlignment.Top
	box.Size = UDim2.new(1, 0, 1, -76)
	local pad = Instance.new("UIPadding")
	pad.PaddingLeft = UDim.new(0, 8)
	pad.PaddingRight = UDim.new(0, 8)
	pad.PaddingTop = UDim.new(0, 6)
	pad.PaddingBottom = UDim.new(0, 6)
	pad.Parent = box
	box:GetPropertyChangedSignal("Text"):Connect(count)

	local note = UIKit.label(
		body,
		"최대 "
			.. SocialLogic.SIGN_LINES
			.. "줄. 로블록스 규정에 따라 걸러진 글이 표지판에 보입니다.",
		12
	)
	note.TextColor3 = UIKit.DIM
	note.TextXAlignment = Enum.TextXAlignment.Left
	note.TextWrapped = false
	note.TextTruncate = Enum.TextTruncate.AtEnd
	note.AnchorPoint = Vector2.new(0, 1)
	note.Position = UDim2.new(0, 0, 1, -44)
	note.Size = UDim2.new(1, -90, 0, 18)

	counter = UIKit.label(body, "", 12)
	counter.TextXAlignment = Enum.TextXAlignment.Right
	counter.TextWrapped = false
	counter.AnchorPoint = Vector2.new(1, 1)
	counter.Position = UDim2.new(1, 0, 1, -44)
	counter.Size = UDim2.fromOffset(86, 18)

	local save = UIKit.button(body, "적기", 14)
	save.AnchorPoint = Vector2.new(1, 1)
	save.Position = UDim2.fromScale(1, 1)
	save.Size = UDim2.fromOffset(120, 34)
	save.Activated:Connect(function()
		send(box.Text)
	end)

	local wipe = UIKit.button(body, "지우기", 13)
	wipe.AnchorPoint = Vector2.new(1, 1)
	wipe.Position = UDim2.new(1, -128, 1, 0)
	wipe.Size = UDim2.fromOffset(90, 34)
	wipe.TextColor3 = UIKit.BAD
	wipe.Activated:Connect(function()
		send("")
	end)

	Net.get("MachineInfo").OnClientEvent:Connect(onInfo)
end

return SignUI
