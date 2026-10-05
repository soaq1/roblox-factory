-- The hub: one shared place per server with the merchants, the mine and the way to the monster
-- island. It is built from plain parts when the server starts, so nobody can edit it. This module
-- also puts a portal on every player's island, since the hub is too far away to walk to.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Defs = require(Shared.Defs)
local Net = require(Shared.Net)
local IslandService = require(script.Parent.IslandService)
local Profile = require(script.Parent.Profile)
local World = require(script.Parent.World)

local HubService = {}

-- A shared place's floor top is this far above its origin, the same as the ground of an island.
HubService.GROUND = 1.5
local GROUND = HubService.GROUND

local STONE = Color3.fromRGB(196, 194, 188)
local TRIM = Color3.fromRGB(72, 70, 67)
local WOOD = Color3.fromRGB(150, 112, 74)
local SKIN = Color3.fromRGB(232, 190, 150)
local HOME = Color3.fromRGB(53, 184, 166) -- the teal of "out": a portal that takes you somewhere calm
local DANGER = Color3.fromRGB(217, 72, 59)

local MERCHANT_COLORS = {
	farmer = Color3.fromRGB(96, 168, 92),
	miner = Color3.fromRGB(88, 110, 140),
	cook = Color3.fromRGB(226, 222, 214),
	builder = Color3.fromRGB(232, 150, 60),
}

-- An anchored part. Everything in the shared places is made of these.
function HubService.block(
	parent: Instance,
	size: Vector3,
	at: CFrame,
	color: Color3,
	material: Enum.Material?
): Part
	local part = Instance.new("Part")
	part.Anchored = true
	part.Size = size
	part.CFrame = at
	part.Color = color
	part.Material = material or Enum.Material.SmoothPlastic
	part.TopSurface = Enum.SurfaceType.Smooth
	part.BottomSurface = Enum.SurfaceType.Smooth
	part.Parent = parent
	return part
end

-- Words floating above a part, readable from a distance.
function HubService.sign(part: BasePart, text: string, height: number): TextLabel
	local gui = Instance.new("BillboardGui")
	gui.Size = UDim2.fromOffset(260, 40)
	gui.StudsOffsetWorldSpace = Vector3.new(0, height, 0)
	gui.MaxDistance = 160
	local label = Instance.new("TextLabel")
	label.Size = UDim2.fromScale(1, 1)
	label.BackgroundTransparency = 1
	label.TextColor3 = Color3.new(1, 1, 1)
	label.TextStrokeTransparency = 0.3
	label.Font = Enum.Font.GothamBold
	label.TextSize = 20
	label.Text = text
	label.Parent = gui
	gui.Parent = part
	return label
end

-- Moves a living player's character. Returns false if there was nobody to move.
function HubService.send(player: Player, at: CFrame): boolean
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	local humanoid = character and character:FindFirstChildOfClass("Humanoid")
	if not character or not root or not root:IsA("BasePart") or not humanoid or humanoid.Health <= 0 then
		return false
	end
	character:PivotTo(at)
	root.AssemblyLinearVelocity = Vector3.zero
	root.AssemblyAngularVelocity = Vector3.zero
	return true
end

-- A doorway with a glowing pane. `at` is the middle of the doorway at ground level; the doorway
-- faces along its Z. Standing close and pressing the key runs `use`. When `solid` is false nothing
-- about it collides or is seen by the build cursor, which is what an island needs: it is not a
-- block, and must not get in the way of building.
function HubService.portal(
	parent: Instance,
	at: CFrame,
	label: string,
	color: Color3,
	solid: boolean,
	use: (Player) -> ()
): Model
	local model = Instance.new("Model")
	model.Name = "Portal"
	local parts = {
		HubService.block(model, Vector3.new(0.8, 7.8, 0.8), at * CFrame.new(-2.4, 3.9, 0), TRIM),
		HubService.block(model, Vector3.new(0.8, 7.8, 0.8), at * CFrame.new(2.4, 3.9, 0), TRIM),
		HubService.block(model, Vector3.new(5.6, 0.8, 0.8), at * CFrame.new(0, 7.4, 0), TRIM),
	}
	local pane =
		HubService.block(model, Vector3.new(4, 7, 0.3), at * CFrame.new(0, 3.5, 0), color, Enum.Material.Neon)
	pane.Name = "Pane"
	pane.Transparency = 0.45
	pane.CanCollide = false
	pane.CanQuery = false
	pane.CanTouch = false
	if not solid then
		for _, part in parts do
			part.CanCollide = false
			part.CanQuery = false
			part.CanTouch = false
		end
	end
	HubService.sign(pane, label, 5.6)

	local prompt = Instance.new("ProximityPrompt")
	prompt.ActionText = "들어가기"
	prompt.ObjectText = label
	prompt.KeyboardKeyCode = Enum.KeyCode.F
	prompt.HoldDuration = 0
	prompt.MaxActivationDistance = 12
	prompt.RequiresLineOfSight = false
	prompt.Parent = pane
	prompt.Triggered:Connect(use)

	model.Parent = parent
	return model
end

-- Where a player stands on arriving in the hub, facing the merchants.
function HubService.arrival(): CFrame
	return CFrame.new(World.HUB_ORIGIN + Vector3.new(0, GROUND + 3, 10))
end

-- Where a player stands on arriving on the monster island, facing its middle.
function HubService.monsterArrival(): CFrame
	return CFrame.new(World.MONSTER_ORIGIN + Vector3.new(0, GROUND + 3, 55))
end

function HubService.toHub(player: Player)
	if HubService.send(player, HubService.arrival()) then
		Profile.notify(
			player,
			"허브에 왔습니다. 상인에게 말을 걸거나 광산에서 캐 보세요"
		)
	end
end

function HubService.toIsland(player: Player)
	local island = IslandService.get(player)
	if island and HubService.send(player, IslandService.spawnCFrame(island)) then
		Profile.notify(player, "내 섬으로 돌아왔습니다")
	end
end

-- A merchant: a small figure behind a counter. Talking to one opens their counter on the client;
-- the shop itself checks the player is still standing near `World.merchantAt[id]`.
local function merchant(parent: Instance, id: string, at: CFrame)
	local color = MERCHANT_COLORS[id] or STONE
	local model = Instance.new("Model")
	model.Name = "Merchant_" .. id
	local body = HubService.block(model, Vector3.new(2.2, 3.2, 1.3), at * CFrame.new(0, 2.6, 0), color)
	body.Name = "Body"
	HubService.block(model, Vector3.new(0.9, 1, 1), at * CFrame.new(-0.55, 0.5, 0), TRIM)
	HubService.block(model, Vector3.new(0.9, 1, 1), at * CFrame.new(0.55, 0.5, 0), TRIM)
	local head = HubService.block(model, Vector3.new(1.7, 1.7, 1.7), at * CFrame.new(0, 5.05, 0), SKIN)
	head.Shape = Enum.PartType.Ball
	HubService.block(model, Vector3.new(2.3, 0.35, 2.3), at * CFrame.new(0, 5.95, 0), color)
	-- the counter stands between the merchant and the middle of the hub (local +Z)
	HubService.block(model, Vector3.new(9, 3, 2), at * CFrame.new(0, 1.5, 4), WOOD)
	HubService.block(model, Vector3.new(9.4, 0.3, 2.6), at * CFrame.new(0, 3.15, 4), TRIM)
	for _, x in { -4.6, 4.6 } do
		HubService.block(model, Vector3.new(0.5, 9, 0.5), at * CFrame.new(x, 4.5, 5), TRIM)
		HubService.block(model, Vector3.new(0.5, 9, 0.5), at * CFrame.new(x, 4.5, -2), TRIM)
	end
	HubService.block(model, Vector3.new(10.4, 0.4, 8), at * CFrame.new(0, 9.2, 1.5), color)
	HubService.sign(head, World.MERCHANT_NAMES[id] or id, 2.2)

	local prompt = Instance.new("ProximityPrompt")
	prompt.ActionText = "말 걸기"
	prompt.ObjectText = World.MERCHANT_NAMES[id] or id
	prompt.KeyboardKeyCode = Enum.KeyCode.F
	prompt.HoldDuration = 0
	prompt.MaxActivationDistance = 12
	prompt.RequiresLineOfSight = false
	prompt.Parent = body
	prompt.Triggered:Connect(function(player)
		Net.get("Shop"):FireClient(player, id)
	end)

	model.Parent = parent
	World.merchantAt[id] = body.Position
end

local function buildHub()
	local folder = Instance.new("Folder")
	folder.Name = "Hub"
	local origin = World.HUB_ORIGIN

	-- The floor reaches further east than west: the mine is on that side.
	HubService.block(folder, Vector3.new(200, 3, 140), CFrame.new(origin + Vector3.new(10, 0, 0)), STONE)
	-- A darker square marks the middle, where players arrive.
	local mark = HubService.block(
		folder,
		Vector3.new(16, 0.2, 16),
		CFrame.new(origin + Vector3.new(0, GROUND + 0.1, 10)),
		TRIM
	)
	mark.CanCollide = false

	-- Merchants stand in a row along the north side, facing the middle.
	for i, id in World.MERCHANTS do
		local x = -30 + (i - 1) * 20
		merchant(folder, id, CFrame.new(origin + Vector3.new(x, GROUND, -40)))
	end

	-- Portals stand along the south side.
	local south = origin + Vector3.new(0, GROUND, 44)
	HubService.portal(
		folder,
		CFrame.new(south + Vector3.new(-16, 0, 0)),
		"내 섬으로",
		HOME,
		true,
		HubService.toIsland
	)
	HubService.portal(
		folder,
		CFrame.new(south + Vector3.new(16, 0, 0)),
		"몬스터 섬 (위험)",
		DANGER,
		true,
		function(player)
			if HubService.send(player, HubService.monsterArrival()) then
				Profile.notify(
					player,
					"몬스터 섬입니다. 슬라임을 잡으면 가끔 "
						.. Defs.name("monster_part")
						.. "이(가) 나옵니다. 쓰러지면 내 섬에서 깨어납니다"
				)
			end
		end
	)

	folder.Parent = Workspace
end

-- The way from an island to the hub. It stands a few steps north of where the player arrives.
local function islandPortal(island)
	if island.folder:FindFirstChild("Portal") then
		return
	end
	local at = CFrame.new(island.origin + Vector3.new(0, GROUND, -12))
	HubService.portal(island.folder, at, "허브로", HOME, false, HubService.toHub)
end

function HubService.start()
	buildHub()
	IslandService.onCreated(islandPortal)
	for _, island in IslandService.all() do
		islandPortal(island)
	end
end

return HubService
