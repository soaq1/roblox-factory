-- The mine in the hub: rocks that anyone can break with a pickaxe. Each gives its ore straight to
-- the miner's bag, comes back after a while, and once in a long while also gives a vein core, the
-- heart of an extractor. A node's toughness is shared: two players on one rock break it together,
-- and whoever lands the last swing takes the ore.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Defs = require(Shared.Defs)
local Inventory = require(Shared.Inventory)
local Net = require(Shared.Net)
local ToolLogic = require(Shared.ToolLogic)
local IslandService = require(script.Parent.IslandService)
local Profile = require(script.Parent.Profile)
local RateLimit = require(script.Parent.RateLimit)
local World = require(script.Parent.World)

local MineService = {}

local GROUND = 1.5 -- the hub's floor top above its origin
local CENTRE = World.HUB_ORIGIN + Vector3.new(70, 0, 0)
local NODE = 4 -- studs across one rock
local REACH = 16 -- how far from a rock a player can be and still hit it
local SWING_GAP = 0.18 -- seconds between swings that count; anything faster is ignored
local WARN_GAP = 2 -- seconds between "your pickaxe is too weak" messages

local ROCK = Color3.fromRGB(128, 126, 122)
local DARK = Color3.fromRGB(86, 84, 82)

-- Which rock stands in each column, west to east: the common ones nearest the entrance.
-- Five rows per column; a number below five leaves the last rows of that column empty.
local COLUMNS = {
	{ kind = "stone", count = 5 },
	{ kind = "stone", count = 5 },
	{ kind = "coal", count = 5 },
	{ kind = "ore_cu", count = 5 },
	{ kind = "ore_fe", count = 5 },
	{ kind = "ore_au", count = 3 },
	{ kind = "ore_dia", count = 2 },
}

type Node = { kind: string, def: ToolLogic.Node, part: Part, hp: number, alive: boolean }

local folder: Folder
local nodes: { [Instance]: Node } = {}
local lastSwing: { [Player]: number } = {}
local lastWarn: { [Player]: number } = {}

local function rock(kind: string, def: ToolLogic.Node, position: Vector3): Part
	local part = Instance.new("Part")
	part.Name = "Node_" .. kind
	part.Anchored = true
	part.Size = Vector3.new(NODE, NODE, NODE)
	part.Position = position
	part.Color = if kind == "stone" then ROCK else DARK
	part.Material = Enum.Material.Slate
	part:SetAttribute("Node", kind)

	-- Lumps of the ore show through the rock. They are for show: the cursor passes through them.
	if kind ~= "stone" then
		local item = Defs.Items[def.item]
		local color = Color3.fromRGB(item.color[1], item.color[2], item.color[3])
		local spots = {
			Vector3.new(1.75, 0.7, -0.6),
			Vector3.new(-1.75, -0.5, 0.7),
			Vector3.new(0.6, 0.4, 1.75),
			Vector3.new(-0.7, -0.6, -1.75),
			Vector3.new(-0.4, 1.75, 0.5),
		}
		for i, spot in spots do
			local lump = Instance.new("Part")
			lump.Anchored = true
			lump.CanCollide = false
			lump.CanQuery = false
			lump.CanTouch = false
			lump.Size = Vector3.new(1.1, 1.1, 1.1)
			lump.CFrame = CFrame.new(position + spot) * CFrame.Angles(i * 0.7, i * 1.3, 0)
			lump.Color = color
			lump.Material = Enum.Material.SmoothPlastic
			lump.Parent = part
		end
	end

	local gui = Instance.new("BillboardGui")
	gui.Size = UDim2.fromOffset(160, 24)
	gui.StudsOffsetWorldSpace = Vector3.new(0, NODE / 2 + 1, 0)
	gui.MaxDistance = 34
	local label = Instance.new("TextLabel")
	label.Size = UDim2.fromScale(1, 1)
	label.BackgroundTransparency = 1
	label.TextColor3 = Color3.new(1, 1, 1)
	label.TextStrokeTransparency = 0.3
	label.Font = Enum.Font.GothamMedium
	label.TextSize = 14
	label.Text = Defs.name(def.item)
	label.Parent = gui
	gui.Parent = part
	return part
end

local function build()
	folder = Instance.new("Folder")
	folder.Name = "Mine"

	-- A darker patch of ground and a wall behind it mark where the mine is.
	local ground = Instance.new("Part")
	ground.Name = "Ground"
	ground.Anchored = true
	ground.Size = Vector3.new(64, 0.2, 54)
	ground.Position = CENTRE + Vector3.new(0, GROUND + 0.1, 0)
	ground.Color = DARK
	ground.Material = Enum.Material.Slate
	ground.Parent = folder
	local wall = Instance.new("Part")
	wall.Name = "Wall"
	wall.Anchored = true
	wall.Size = Vector3.new(3, 14, 54)
	wall.Position = CENTRE + Vector3.new(33.5, GROUND + 7, 0)
	wall.Color = DARK
	wall.Material = Enum.Material.Slate
	wall.Parent = folder

	local gui = Instance.new("BillboardGui")
	gui.Size = UDim2.fromOffset(360, 40)
	gui.StudsOffsetWorldSpace = Vector3.new(-62, 2, 0)
	gui.MaxDistance = 160
	local label = Instance.new("TextLabel")
	label.Size = UDim2.fromScale(1, 1)
	label.BackgroundTransparency = 1
	label.TextColor3 = Color3.new(1, 1, 1)
	label.TextStrokeTransparency = 0.3
	label.Font = Enum.Font.GothamBold
	label.TextSize = 20
	label.Text = "광산 · 좌클릭을 누르고 있으면 캡니다"
	label.Parent = gui
	gui.Parent = wall

	local top = GROUND + 0.2
	for column, entry in COLUMNS do
		local def = ToolLogic.NODES[entry.kind]
		for row = 1, entry.count do
			local position = CENTRE + Vector3.new(-24 + (column - 1) * 8, top + NODE / 2, -18 + (row - 1) * 9)
			local part = rock(entry.kind, def, position)
			part.Parent = folder
			nodes[part] = { kind = entry.kind, def = def, part = part, hp = def.hardness, alive = true }
		end
	end
	folder.Parent = Workspace
end

-- Says something to a player, but not more often than every couple of seconds.
local function tell(player: Player, text: string)
	local now = os.clock()
	if now - (lastWarn[player] or 0) >= WARN_GAP then
		lastWarn[player] = now
		Profile.notify(player, text)
	end
end

local function onMine(player: Player, target: any)
	if typeof(target) ~= "Instance" then
		return
	end
	local node = nodes[target]
	local island = IslandService.get(player)
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	if not node or not node.alive or not island or not root or not root:IsA("BasePart") then
		return
	end
	if (node.part.Position - root.Position).Magnitude > REACH then
		return
	end
	local swing = ToolLogic.nodeSwing(node.kind, island.bag)
	if not swing then
		local needs = ToolLogic.nodeNeeds(node.kind)
		tell(
			player,
			Defs.name(node.def.item)
				.. ": "
				.. Defs.name(needs or "pick_wood")
				.. " 이상이 있어야 캘 수 있습니다"
		)
		return
	end
	local now = os.clock()
	if now - (lastSwing[player] or 0) < SWING_GAP then
		return
	end
	lastSwing[player] = now

	node.hp -= swing
	if node.hp > 0 then
		Net.get("World"):FireClient(player, { kind = "progress", fraction = 1 - node.hp / node.def.hardness })
		return
	end
	Net.get("World"):FireClient(player, { kind = "progress", fraction = 1 })

	-- Broken: out of the world until it grows back.
	node.alive = false
	node.part.Parent = nil
	task.delay(node.def.respawn, function()
		node.hp = node.def.hardness
		node.alive = true
		node.part.Parent = folder
	end)

	Inventory.add(island.bag, node.def.item, 1)
	local core = ToolLogic.rollCore(node.kind, math.random())
	if core then
		Inventory.add(island.bag, core, 1)
		Profile.notify(
			player,
			Defs.name(core)
				.. "을(를) 얻었습니다! 빈 추출기와 합치면 그 광물이 섬에서 나옵니다"
		)
	end
	Profile.push(island)
end

function MineService.start()
	build()
	Net.get("WorldAct").OnServerEvent:Connect(function(player: Player, action: any, target: any)
		if action == "mine" and RateLimit.allow(player) then
			onMine(player, target)
		end
	end)
	Players.PlayerRemoving:Connect(function(player)
		lastSwing[player] = nil
		lastWarn[player] = nil
	end)
end

return MineService
