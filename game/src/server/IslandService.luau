-- One island per player: where it sits in the world and what is in each cell.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = require(Shared.Config)
local Defs = require(Shared.Defs)
local Grid = require(Shared.Grid)
local IslandGen = require(Shared.IslandGen)

local IslandService = {}

export type Cell = { kind: "block" | "machine", id: string, part: Instance?, machine: any? }
export type Island = {
	owner: Player,
	slot: number,
	origin: Vector3,
	folder: Folder,
	blocksFolder: Folder,
	machinesFolder: Folder,
	spawn: SpawnLocation,
	cells: { [string]: Cell },
	bag: { [string]: number },
	mode: string, -- "creative" or "survival"
	coins: number,
	tiers: { [string]: number }, -- workbench kind -> tier, for kinds raised above 1
	handFuel: number, -- heat left over from the last fire lit for hand work
	canSave: boolean,
}

local islands: { [Player]: Island } = {}
local slots: { [number]: Player } = {}

local CELL = Config.CELL
local BLOCK_SIZE = Vector3.new(CELL, CELL, CELL)

function IslandService.create(player: Player): Island
	local slot = 1
	while slots[slot] do
		slot += 1
	end
	slots[slot] = player

	local folder = Instance.new("Folder")
	folder.Name = "Island_" .. player.UserId
	local blocksFolder = Instance.new("Folder")
	blocksFolder.Name = "Blocks"
	blocksFolder.Parent = folder
	local machinesFolder = Instance.new("Folder")
	machinesFolder.Name = "Machines"
	machinesFolder.Parent = folder
	folder.Parent = Workspace

	-- A thin pad the player always arrives on. It is not a block, so it cannot be broken: even if
	-- the ground under it is dug away there is still somewhere to stand.
	local origin = Vector3.new(slot * Config.ISLAND_SPACING, 0, 0)
	local s = IslandGen.SPAWN
	local pad = Instance.new("SpawnLocation")
	pad.Name = "SpawnPad"
	pad.Anchored = true
	pad.Neutral = true
	pad.Duration = 0
	pad.Size = Vector3.new(CELL, 0.1, CELL)
	pad.Position = origin + Vector3.new(s.x * CELL, (s.y - 0.5) * CELL + 0.05, s.z * CELL)
	pad.Material = Enum.Material.SmoothPlastic
	pad.Color = Color3.fromRGB(228, 225, 219)
	pad.Transparency = 0.5
	pad.Parent = folder
	player.RespawnLocation = pad

	local island: Island = {
		owner = player,
		slot = slot,
		origin = origin,
		folder = folder,
		blocksFolder = blocksFolder,
		machinesFolder = machinesFolder,
		spawn = pad,
		cells = {},
		bag = {},
		mode = Config.START_MODE,
		coins = Config.START_COINS,
		tiers = {},
		handFuel = 0,
		-- Stays false until the island has finished loading, so a half-built island is never saved
		-- over the real one.
		canSave = false,
	}
	islands[player] = island
	player:SetAttribute("IslandOrigin", island.origin)
	return island
end

function IslandService.get(player: Player): Island?
	return islands[player]
end

function IslandService.all(): { [Player]: Island }
	return islands
end

function IslandService.destroy(player: Player)
	local island = islands[player]
	if not island then
		return
	end
	islands[player] = nil
	slots[island.slot] = nil
	island.folder:Destroy()
end

function IslandService.cellCenter(island: Island, x: number, y: number, z: number): Vector3
	return island.origin + Vector3.new(x * CELL, y * CELL, z * CELL)
end

function IslandService.spawnCFrame(island: Island): CFrame
	local s = IslandGen.SPAWN
	return CFrame.new(IslandService.cellCenter(island, s.x, s.y, s.z) + Vector3.new(0, 2, 0))
end

-- Is this world position inside the stretch of world that belongs to the island?
function IslandService.owns(island: Island, position: Vector3): boolean
	return math.abs(position.X - island.origin.X) < Config.ISLAND_SPACING / 2
end

function IslandService.setBlock(island: Island, x: number, y: number, z: number, id: string): boolean
	local key = Grid.key(x, y, z)
	local def = Defs.Blocks[id]
	if island.cells[key] or not def or not Grid.inBounds(x, y, z, Config.MAX_COORD) then
		return false
	end
	local part = Instance.new("Part")
	part.Name = key
	part.Anchored = true
	part.Size = BLOCK_SIZE
	part.Material = Enum.Material.SmoothPlastic
	part.Color = Color3.fromRGB(def.color[1], def.color[2], def.color[3])
	part.Transparency = def.transparency
	part.Position = IslandService.cellCenter(island, x, y, z)
	-- Blocks whose top differs from their sides (grass, logs, farmland) get a thin cap.
	local top = def.top
	if
		math.abs(top[1] - def.color[1])
			+ math.abs(top[2] - def.color[2])
			+ math.abs(top[3] - def.color[3])
		> 60
	then
		local cap = Instance.new("Part")
		cap.Name = "Cap"
		cap.Anchored = true
		cap.CanCollide = false
		cap.CanQuery = false
		cap.CanTouch = false
		cap.Size = Vector3.new(CELL + 0.02, 0.45, CELL + 0.02)
		cap.Material = Enum.Material.SmoothPlastic
		cap.Color = Color3.fromRGB(top[1], top[2], top[3])
		cap.Position = part.Position + Vector3.new(0, CELL / 2 - 0.22, 0)
		cap.Parent = part
	end
	part.Parent = island.blocksFolder
	island.cells[key] = { kind = "block", id = id, part = part }
	return true
end

function IslandService.clearCell(island: Island, key: string)
	local cell = island.cells[key]
	if not cell then
		return
	end
	island.cells[key] = nil
	if cell.part then
		cell.part:Destroy()
	end
end

return IslandService
