-- What the player does away from their own island: mining rocks in the hub and fighting on the
-- monster island. Holding the left button on a rock or a monster keeps swinging at it. This module
-- also draws the bar that shows how far along a rock or a block is; the island's own blocks are
-- handled by BuildController, and the two never overlap because rocks and monsters are never on an
-- island.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")
local Workspace = game:GetService("Workspace")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Net = require(Shared:WaitForChild("Net"))
local HandView = require(script.Parent.HandView)
local Screens = require(script.Parent.Screens)
local UIKit = require(script.Parent.UIKit)

local WorldController = {}

local player = Players.LocalPlayer
local MINE_SECONDS = 0.25 -- how often a held button swings at a rock
local ATTACK_SECONDS = 0.4 -- and at a monster
local REACH = 16 -- further than this and the server would refuse anyway
local BAR_SECONDS = 1.2 -- the bar goes away this long after the last swing

local held = false
local sinceSwing = 0
local bar: Frame
local fill: Frame
local barToken = 0

-- What the cursor is on: "mine" with a rock, "attack" with a monster, or nothing.
local function aim(): (string?, Instance?)
	local camera = Workspace.CurrentCamera
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	if not camera or not character or not root or not root:IsA("BasePart") then
		return nil, nil
	end
	local ignore: { Instance } = { character }
	local items = Workspace:FindFirstChild("Items")
	if items then
		table.insert(ignore, items)
	end
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = ignore
	local mouse = UserInputService:GetMouseLocation()
	local ray = camera:ViewportPointToRay(mouse.X, mouse.Y)
	local hit = Workspace:Raycast(ray.Origin, ray.Direction * 400, params)
	if not hit or (hit.Position - root.Position).Magnitude > REACH + 4 then
		return nil, nil
	end
	if hit.Instance:GetAttribute("Node") then
		return "mine", hit.Instance
	end
	local model = hit.Instance:FindFirstAncestorOfClass("Model")
	if model and model:GetAttribute("Monster") then
		return "attack", model
	end
	return nil, nil
end

-- Swings once at whatever is under the cursor. Returns how long to wait before the next swing,
-- or nil if there was nothing to swing at.
local function swing(): number?
	if Screens.anyOpen() then
		return nil
	end
	local action, what = aim()
	if not action or not what then
		return nil
	end
	HandView.swing()
	Net.get("WorldAct"):FireServer(action, what)
	return if action == "mine" then MINE_SECONDS else ATTACK_SECONDS
end

local gap = MINE_SECONDS -- seconds until the held button swings again

local function showProgress(fraction: number)
	barToken += 1
	local token = barToken
	fill.Size = UDim2.fromScale(math.clamp(fraction, 0, 1), 1)
	bar.Visible = true
	-- A full bar means the thing has just broken, so it need not linger.
	task.delay(if fraction >= 1 then 0.2 else BAR_SECONDS, function()
		if token == barToken then
			bar.Visible = false
		end
	end)
end

function WorldController.init(_hotbar)
	bar = Instance.new("Frame")
	bar.Name = "Progress"
	bar.AnchorPoint = Vector2.new(0.5, 0.5)
	bar.Position = UDim2.fromScale(0.5, 0.62)
	bar.Size = UDim2.fromOffset(200, 12)
	bar.BackgroundColor3 = UIKit.BACK
	bar.BorderSizePixel = 0
	bar.Visible = false
	bar.Parent = Screens.gui()
	UIKit.round(bar, 6)
	UIKit.stroke(bar)
	fill = Instance.new("Frame")
	fill.Size = UDim2.fromScale(0, 1)
	fill.BackgroundColor3 = UIKit.PICK
	fill.BorderSizePixel = 0
	fill.Parent = bar
	UIKit.round(fill, 6)

	Net.get("World").OnClientEvent:Connect(function(message)
		if type(message) == "table" and message.kind == "progress" and type(message.fraction) == "number" then
			showProgress(message.fraction)
		end
	end)

	UserInputService.InputBegan:Connect(function(input, handledByUi)
		if handledByUi or input.UserInputType ~= Enum.UserInputType.MouseButton1 then
			return
		end
		local first = swing()
		if first then
			held = true
			sinceSwing = 0
			gap = first
		end
	end)
	UserInputService.InputEnded:Connect(function(input)
		if input.UserInputType == Enum.UserInputType.MouseButton1 then
			held = false
		end
	end)
	RunService.RenderStepped:Connect(function(dt)
		if not held then
			return
		end
		sinceSwing += dt
		if sinceSwing < gap then
			return
		end
		sinceSwing = 0
		-- Keep the button's hold alive even when the cursor is between targets for a moment:
		-- a rock that has just broken leaves nothing to hit until the cursor reaches the next.
		gap = swing() or MINE_SECONDS
	end)
end

return WorldController
