-- Handles requests to place, break and pick up. Nothing a client sends is trusted:
-- every request is checked for type, range, ownership and rate before anything changes.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Players = game:GetService("Players")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = require(Shared.Config)
local Defs = require(Shared.Defs)
local Grid = require(Shared.Grid)
local Inventory = require(Shared.Inventory)
local Net = require(Shared.Net)
local IslandService = require(script.Parent.IslandService)
local ItemService = require(script.Parent.ItemService)
local MachineService = require(script.Parent.MachineService)

local PlacementService = {}

-- A small allowance that refills over time. Requests beyond it are dropped.
local buckets: { [Player]: { tokens: number, at: number } } = {}

local function allowed(player: Player): boolean
	local now = os.clock()
	local bucket = buckets[player]
	if not bucket then
		bucket = { tokens = Config.RATE_PER_SECOND, at = now }
		buckets[player] = bucket
	end
	bucket.tokens =
		math.min(Config.RATE_PER_SECOND, bucket.tokens + (now - bucket.at) * Config.RATE_PER_SECOND)
	bucket.at = now
	if bucket.tokens < 1 then
		return false
	end
	bucket.tokens -= 1
	return true
end

local function rootPosition(player: Player): Vector3?
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	if root and root:IsA("BasePart") then
		return root.Position
	end
	return nil
end

-- Returns the island when the player may edit this cell.
local function editable(player: Player, x: any, y: any, z: any): IslandService.Island?
	if not allowed(player) then
		return nil
	end
	if not (Grid.isInt(x) and Grid.isInt(y) and Grid.isInt(z)) then
		return nil
	end
	if not Grid.inBounds(x, y, z, Config.MAX_COORD) then
		return nil
	end
	local island = IslandService.get(player)
	local position = rootPosition(player)
	if not island or not position then
		return nil
	end
	local center = IslandService.cellCenter(island, x, y, z)
	if (center - position).Magnitude > Config.REACH + Config.CELL then
		return nil
	end
	return island
end

local function place(player: Player, id: any, x: any, y: any, z: any, dir: any)
	local island = editable(player, x, y, z)
	if not island or not Defs.isPlaceable(id) then
		return
	end
	if island.cells[Grid.key(x, y, z)] then
		return
	end
	if Defs.isBlock(id) then
		IslandService.setBlock(island, x, y, z, id)
	elseif Grid.isDir(dir) then
		MachineService.create(island, id, x, y, z, dir, nil)
	end
end

local function breakCell(player: Player, x: any, y: any, z: any)
	local island = editable(player, x, y, z)
	if not island then
		return
	end
	local key = Grid.key(x, y, z)
	local cell = island.cells[key]
	if not cell then
		return
	end
	if cell.kind == "machine" then
		MachineService.remove(cell.machine, true)
	else
		IslandService.clearCell(island, key)
	end
end

local function pickup(player: Player)
	local island = IslandService.get(player)
	local position = rootPosition(player)
	if not island or not position or not allowed(player) then
		return
	end
	local part = ItemService.nearest(position, Config.PICKUP_RANGE)
	if not part then
		return
	end
	local id, count = ItemService.info(part)
	if id then
		Inventory.add(island.bag, id, ItemService.take(part, count))
		Net.get("Bag"):FireClient(player, island.bag)
	end
end

function PlacementService.start()
	Net.get("Place").OnServerEvent:Connect(place)
	Net.get("Break").OnServerEvent:Connect(breakCell)
	Net.get("Pickup").OnServerEvent:Connect(pickup)
	Players.PlayerRemoving:Connect(function(player)
		buckets[player] = nil
	end)
end

return PlacementService
