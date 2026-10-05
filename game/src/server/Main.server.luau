-- Start-up: bring the services up, then give each arriving player an island.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Defs = require(Shared.Defs)
local Inventory = require(Shared.Inventory)
local IslandGen = require(Shared.IslandGen)
local Net = require(Shared.Net)
local DebugService = require(script.Parent.DebugService)
local IslandService = require(script.Parent.IslandService)
local ItemService = require(script.Parent.ItemService)
local MachineService = require(script.Parent.MachineService)
local PlacementService = require(script.Parent.PlacementService)
local SaveService = require(script.Parent.SaveService)

local BATCH = 400 -- blocks built before letting the server breathe

local function buildStarter(island: IslandService.Island)
	for _, b in IslandGen.generate() do
		IslandService.setBlock(island, b.x, b.y, b.z, b.id)
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
	island.bag = Inventory.sanitize(saved.bag, Defs.isItem)
	return true
end

local function spawnCharacter(player: Player, island: IslandService.Island)
	player.CharacterAdded:Connect(function(character)
		local root = character:WaitForChild("HumanoidRootPart", 10)
		if root then
			character:PivotTo(IslandService.spawnCFrame(island))
		end
		local humanoid = character:WaitForChild("Humanoid", 10)
		if humanoid and humanoid:IsA("Humanoid") then
			humanoid.Died:Once(function()
				task.wait(2)
				if player.Parent == Players and IslandService.get(player) == island then
					player:LoadCharacter()
				end
			end)
		end
	end)
	player:LoadCharacter()
end

local function onPlayerAdded(player: Player)
	local island = IslandService.create(player)
	local result = SaveService.load(player)
	if player.Parent ~= Players then
		return -- left while loading; PlayerRemoving has already cleaned up
	end

	if result.status == "loaded" and result.island then
		if not buildSaved(player, island, result.island) then
			return
		end
		island.canSave = true
		if result.skipped > 0 then
			Net.get("Notify"):FireClient(
				player,
				"저장된 섬에서 읽을 수 없는 항목 "
					.. result.skipped
					.. "개를 건너뛰었습니다."
			)
		end
	else
		buildStarter(island)
		if result.status == "new" then
			island.canSave = true
		else
			-- The stored island exists but could not be read. Play on a fresh island without
			-- saving, so the stored copy is left untouched.
			Net.get("Notify"):FireClient(
				player,
				"저장된 섬을 불러오지 못했습니다. 이번 접속은 저장되지 않습니다."
			)
		end
	end

	Net.get("Bag"):FireClient(player, island.bag)
	spawnCharacter(player, island)
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

MachineService.start()
PlacementService.start()
SaveService.start()
DebugService.start()

Players.PlayerAdded:Connect(onPlayerAdded)
Players.PlayerRemoving:Connect(onPlayerRemoving)
for _, player in Players:GetPlayers() do
	task.spawn(onPlayerAdded, player)
end
