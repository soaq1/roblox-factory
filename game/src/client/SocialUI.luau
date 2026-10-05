-- Other players: the card that opens when one is clicked, and asking the one standing next to you
-- to trade. Close to another player a marker over their head shows that T is live; pressing T (or
-- the marker) asks them. With nobody near, T opens the trade screen as before.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")
local Workspace = game:GetService("Workspace")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Net = require(Shared:WaitForChild("Net"))
local SocialLogic = require(Shared:WaitForChild("SocialLogic"))
local Screens = require(script.Parent.Screens)
local UIKit = require(script.Parent.UIKit)

local SocialUI = {}

local player = Players.LocalPlayer
local NEAR_RANGE = 12 -- studs within which another player can be asked with T (a placeholder)
local CLICK_RANGE = 300 -- how far away a player can be clicked for their card
local LOOK_SECONDS = 0.2 -- how often to look for who is nearest

local cardBody: Frame
local marker: BillboardGui
local markerButton: TextButton
local near: Player? = nil
local trading = false
local askedMe: { [number]: boolean } = {} -- user ids with a request waiting on me
local sinceLook = 0

local function rootOf(who: Player): BasePart?
	local character = who.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	return if root and root:IsA("BasePart") then root else nil
end

local function ask(target: Player)
	Net.get("TradeAct"):FireServer("ask", target)
end

-- ---------------------------------------------------------------- the card

local function showCard(card: any)
	if type(card) ~= "table" or type(card.userId) ~= "number" then
		return
	end
	local target = Players:GetPlayerByUserId(card.userId)
	if not target then
		return
	end
	UIKit.clear(cardBody)

	local display = tostring(card.display or card.name)
	local name = UIKit.label(cardBody, display, 20)
	name.TextXAlignment = Enum.TextXAlignment.Left
	name.TextWrapped = false
	name.TextTruncate = Enum.TextTruncate.AtEnd
	name.Size = UDim2.new(1, 0, 0, 26)

	local account = UIKit.label(cardBody, "@" .. tostring(card.name), 13)
	account.TextColor3 = UIKit.DIM
	account.TextXAlignment = Enum.TextXAlignment.Left
	account.TextWrapped = false
	account.Position = UDim2.fromOffset(0, 28)
	account.Size = UDim2.new(1, 0, 0, 18)

	local where = UIKit.label(cardBody, SocialLogic.whereText(card), 14)
	where.TextXAlignment = Enum.TextXAlignment.Left
	where.TextYAlignment = Enum.TextYAlignment.Top
	where.TextColor3 = if card.private then UIKit.DIM else UIKit.TEXT
	where.Position = UDim2.fromOffset(0, 56)
	where.Size = UDim2.new(1, 0, 0, 40)

	local trade = UIKit.button(cardBody, "거래하기", 14)
	trade.AnchorPoint = Vector2.new(0, 1)
	trade.Position = UDim2.fromScale(0, 1)
	trade.Size = UDim2.fromOffset(130, 36)
	trade.Activated:Connect(function()
		Screens.close("playercard")
		ask(target)
	end)

	-- A private profile offers nothing but the trade.
	if card.canVisit and not card.private then
		local visit = UIKit.button(cardBody, "섬 구경", 14)
		visit.AnchorPoint = Vector2.new(0, 1)
		visit.Position = UDim2.new(0, 138, 1, 0)
		visit.Size = UDim2.fromOffset(110, 36)
		visit.Activated:Connect(function()
			Screens.close("playercard")
			Net.get("VisitAct"):FireServer("go", card.userId)
		end)
	end
	Screens.open("playercard")
end

-- The other player whose body is under a point on the screen, if any.
local function playerAt(ray: Ray): Player?
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	local ignore: { Instance } = {}
	if player.Character then
		table.insert(ignore, player.Character)
	end
	local items = Workspace:FindFirstChild("Items")
	if items then
		table.insert(ignore, items)
	end
	params.FilterDescendantsInstances = ignore
	local hit = Workspace:Raycast(ray.Origin, ray.Direction * CLICK_RANGE, params)
	local node: Instance? = hit and hit.Instance
	-- Hats and tools are models inside the character, so climb until a character is found.
	while node and node ~= Workspace do
		if node:IsA("Model") then
			local owner = Players:GetPlayerFromCharacter(node)
			if owner then
				return if owner ~= player then owner else nil
			end
		end
		node = node.Parent
	end
	return nil
end

local function clicked(ray: Ray)
	if Screens.anyOpen() then
		return
	end
	local target = playerAt(ray)
	if target then
		Net.get("PlayerAct"):FireServer("info", target)
	end
end

-- ---------------------------------------------------------------- the player next to you

local function refreshMarker()
	local target = near
	local root = target and rootOf(target)
	if not target or not root or trading then
		marker.Enabled = false
		marker.Adornee = nil :: any
		return
	end
	local keyboard = UserInputService.KeyboardEnabled
	local words = if askedMe[target.UserId] then "거래 받기" else "거래 청하기"
	markerButton.Text = if keyboard then "T  " .. words else words
	marker.Adornee = root
	marker.Enabled = true
end

local function look(dt: number)
	sinceLook += dt
	if sinceLook < LOOK_SECONDS then
		return
	end
	sinceLook = 0
	local mine = rootOf(player)
	local found: Player? = nil
	if mine then
		local spots = {}
		for _, other in Players:GetPlayers() do
			local root = if other ~= player then rootOf(other) else nil
			if root then
				local at = root.Position
				table.insert(spots, { id = other.UserId, x = at.X, y = at.Y, z = at.Z })
			end
		end
		local at = mine.Position
		local id = SocialLogic.nearest(at.X, at.Y, at.Z, spots, NEAR_RANGE)
		found = if id then Players:GetPlayerByUserId(id) else nil
	end
	near = found
	refreshMarker()
end

-- T: ask the player beside you, or failing that open (or close) the trade screen.
local function onT()
	if Screens.isOpen("trade") then
		Screens.close("trade")
	elseif near and not trading and not Screens.anyOpen() then
		ask(near)
	else
		Screens.toggle("trade")
	end
end

local function onTrade(payload: any)
	if payload == nil then
		trading = false
	elseif type(payload) == "table" then
		if type(payload.request) == "table" and type(payload.request.id) == "number" then
			askedMe[payload.request.id] = true
		elseif type(payload.withdrawn) == "number" then
			askedMe[payload.withdrawn] = nil
		elseif payload.you == "a" or payload.you == "b" then
			trading = true
			table.clear(askedMe)
		end
	end
	refreshMarker()
end

function SocialUI.init(_hotbar)
	local _, body = UIKit.window("playercard", "플레이어", 360, 220)
	cardBody = body

	-- A button floating over the nearby player. It has to live in PlayerGui to be pressable.
	marker = Instance.new("BillboardGui")
	marker.Name = "TradeMarker"
	marker.ResetOnSpawn = false
	marker.Active = true
	marker.AlwaysOnTop = true
	marker.Enabled = false
	marker.Size = UDim2.fromOffset(150, 34)
	marker.StudsOffsetWorldSpace = Vector3.new(0, 4.6, 0)
	marker.MaxDistance = NEAR_RANGE * 3
	marker.Parent = player:WaitForChild("PlayerGui")
	markerButton = UIKit.button(marker, "", 14)
	markerButton.Size = UDim2.fromScale(1, 1)
	markerButton.BackgroundColor3 = UIKit.BACK
	UIKit.stroke(markerButton, UIKit.PICK, 2)
	markerButton.Activated:Connect(function()
		if near and not trading then
			ask(near)
		end
	end)

	Net.get("PlayerInfo").OnClientEvent:Connect(showCard)
	Net.get("Trade").OnClientEvent:Connect(onTrade)
	Screens.onKey(Enum.KeyCode.T, onT)
	RunService.Heartbeat:Connect(look)

	UserInputService.InputBegan:Connect(function(input, handled)
		if handled or input.UserInputType ~= Enum.UserInputType.MouseButton1 then
			return
		end
		local camera = Workspace.CurrentCamera
		if camera then
			local at = UserInputService:GetMouseLocation()
			clicked(camera:ViewportPointToRay(at.X, at.Y))
		end
	end)
	UserInputService.TouchTapInWorld:Connect(function(position, handled)
		local camera = Workspace.CurrentCamera
		if camera and not handled then
			clicked(camera:ScreenPointToRay(position.X, position.Y))
		end
	end)
	Players.PlayerRemoving:Connect(function(gone)
		askedMe[gone.UserId] = nil
		if near == gone then
			near = nil
			refreshMarker()
		end
	end)
end

return SocialUI
