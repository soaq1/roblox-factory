-- Start-up: bring the services up, then give each arriving player an island.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = require(Shared.Config)
local IslandGen = require(Shared.IslandGen)
local Net = require(Shared.Net)
local Commands = require(script.Parent.Commands)
local CraftService = require(script.Parent.CraftService)
local DebugService = require(script.Parent.DebugService)
local GameCommands = require(script.Parent.GameCommands)
local IslandService = require(script.Parent.IslandService)
local MachineActs = require(script.Parent.MachineActs)
local ItemService = require(script.Parent.ItemService)
local MachineService = require(script.Parent.MachineService)
local PlacementService = require(script.Parent.PlacementService)
local Profile = require(script.Parent.Profile)
local SaveService = require(script.Parent.SaveService)
local TradeService = require(script.Parent.TradeService)

local BATCH = 400 -- blocks built before letting the server breathe
local FALL_DEPTH = 90 -- studs below the island at which a falling player is brought back

local function buildStarter(island: IslandService.Island)
	for _, b in IslandGen.generate() do
		IslandService.setBlock(island, b.x, b.y, b.z, b.id)
	end
	for _, t in IslandGen.TREES do
		MachineService.create(island, "tree", t.x, t.y, t.z, 0, nil)
	end
end

-- Returns false if the player left while the island was still being built.
local function buildSaved(player: Player, island: IslandService.Island, saved): boolean
	for i, b in saved.blocks do
		IslandService.setBlock(island, b.x, b.y, b.z, b.id)
		if i % BATCH == 0 then
			task.wait()
			if IslandService.get(player) ~= island then
				return false
			end
		end
	end
	for _, m in saved.machines do
		MachineService.create(island, m.id, m.x, m.y, m.z, m.d, m.s)
	end
	Profile.load(island, saved.bag, saved.profile)
	return true
end

local function putOnIsland(player: Player, island: IslandService.Island)
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	if character and root and root:IsA("BasePart") then
		character:PivotTo(IslandService.spawnCFrame(island))
		root.AssemblyLinearVelocity = Vector3.zero
	end
end

-- Characters do not load on their own in this game (the island has to exist first), so this loop
-- owns the player's body: it loads one when there is none or it has died, and brings back anyone
-- who has fallen off the island.
local function keepCharacter(player: Player, island: IslandService.Island)
	local deadSince: number? = nil
	while IslandService.get(player) == island do
		local character = player.Character
		local humanoid = character and character:FindFirstChildOfClass("Humanoid")
		local root = character and character:FindFirstChild("HumanoidRootPart")
		local alive = character ~= nil and character.Parent ~= nil and humanoid ~= nil and humanoid.Health > 0

		if not alive then
			local since = deadSince or os.clock()
			deadSince = since
			if os.clock() - since >= 2 or character == nil then
				deadSince = nil
				-- LoadCharacter waits until the body is placed, so moving it afterwards sticks.
				local ok = pcall(player.LoadCharacter, player)
				if ok and IslandService.get(player) == island then
					putOnIsland(player, island)
				end
			end
		else
			deadSince = nil
			if root and root:IsA("BasePart") and root.Position.Y < island.origin.Y - FALL_DEPTH then
				putOnIsland(player, island)
			end
		end
		task.wait(0.5)
	end
end

local function onPlayerAdded(player: Player)
	local island = IslandService.create(player)
	local result = SaveService.load(player)
	if IslandService.get(player) ~= island then
		return -- left while loading; PlayerRemoving has already cleaned up
	end

	if result.status == "loaded" and result.island then
		if not buildSaved(player, island, result.island) then
			return
		end
		-- If anything in the stored island could not be read, do not save this session: writing
		-- back would erase the unreadable parts for good.
		island.canSave = result.skipped == 0
		if result.skipped > 0 then
			Net.get("Notify"):FireClient(
				player,
				"저장된 섬에서 읽을 수 없는 항목이 "
					.. result.skipped
					.. "개 있습니다. 이번 접속은 저장되지 않습니다."
			)
		end
	else
		buildStarter(island)
		island.bag = table.clone(Config.START_ITEMS)
		if result.status == "new" then
			island.canSave = true
		else
			Net.get("Notify"):FireClient(
				player,
				"저장된 섬을 불러오지 못했습니다. 이번 접속은 저장되지 않습니다."
			)
		end
	end

	Profile.ensureTool(island)
	Profile.push(island)
	island.extra.ready = true
	Net.get("Prefs"):FireClient(player, island.prefs)
	keepCharacter(player, island)
end

local function onPlayerRemoving(player: Player)
	local island = IslandService.get(player)
	if not island then
		return
	end
	SaveService.save(player)
	MachineService.removeIsland(island)
	ItemService.clearWhere(function(part)
		return not IslandService.owns(island, part.Position)
	end)
	IslandService.destroy(player)
end

Commands.start()
ItemService.start()
MachineService.start()
PlacementService.start()
CraftService.start()
TradeService.start()
SaveService.start()
DebugService.start()
GameCommands.start()
MachineActs.start()
-- Larger systems, each in its own file with a start() of its own.
for _, name in
	{
		"DayCycle",
		"HubService",
		"MineService",
		"MonsterService",
		"ShopService",
		"VisitService",
		"PowerService",
		"PrefsService",
		"SocialService",
	}
do
	local source = script.Parent:FindFirstChild(name)
	if source and source:IsA("ModuleScript") then
		local ok, err = pcall(function()
			(require(source) :: any).start()
		end)
		if not ok then
			warn(name .. " did not start: " .. tostring(err))
		end
	end
end

Players.PlayerAdded:Connect(onPlayerAdded)
Players.PlayerRemoving:Connect(onPlayerRemoving)
for _, player in Players:GetPlayers() do
	task.spawn(onPlayerAdded, player)
end
