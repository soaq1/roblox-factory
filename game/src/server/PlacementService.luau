-- Handles requests to place, break and pick up. Nothing a client sends is trusted:
-- every request is checked for type, range, ownership and rate before anything changes.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = require(Shared.Config)
local Defs = require(Shared.Defs)
local Grid = require(Shared.Grid)
local Inventory = require(Shared.Inventory)
local Net = require(Shared.Net)
local ToolLogic = require(Shared.ToolLogic)
local IslandService = require(script.Parent.IslandService)
local ItemService = require(script.Parent.ItemService)
local MachineService = require(script.Parent.MachineService)
local Profile = require(script.Parent.Profile)
local RateLimit = require(script.Parent.RateLimit)

local PlacementService = {}

local Stock = Profile.Stock
local allowed = RateLimit.allow

local SWING_GAP = 0.15 -- seconds between swings that count; anything faster is ignored
local SWING_KEEP = 2 -- a pause longer than this and the block is whole again

-- Each player's run of swings at the block they are breaking.
local swings: { [Player]: ToolLogic.Swing } = {}

-- In survival mode, the bag key that will pay for placing `entry`, or nil if the bag has none.
-- In creative mode nothing is paid, and this returns false.
local function payment(island: IslandService.Island, entry: string): (string | boolean)?
	if island.mode ~= "survival" then
		return false
	end
	for _, key in Stock.placeCost(entry) do
		if (island.bag[key] or 0) >= 1 then
			return key
		end
	end
	return nil
end

local function settle(island: IslandService.Island, key: string | boolean)
	if type(key) == "string" then
		Inventory.remove(island.bag, key, 1)
		Profile.push(island)
	end
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

-- Some things only go on particular ground: a sapling on grass or dirt, a crop on farmland.
local function groundAllows(island: IslandService.Island, def, x: number, y: number, z: number): boolean
	if not def.needsBelow then
		return true
	end
	local below = island.cells[Grid.key(x, y - 1, z)]
	return below ~= nil and below.kind == "block" and table.find(def.needsBelow, below.id) ~= nil
end

local function place(player: Player, id: any, x: any, y: any, z: any, dir: any)
	local island = editable(player, x, y, z)
	if not island or not Defs.isPlaceable(id) then
		return
	end
	local cost = payment(island, id)
	if cost == nil then
		Net.get("Notify"):FireClient(player, "가방에 " .. Defs.name(id) .. "이(가) 없습니다")
		return
	end
	if Defs.isBlock(id) then
		if not island.cells[Grid.key(x, y, z)] and IslandService.setBlock(island, x, y, z, id) then
			settle(island, cost)
		end
		return
	end
	local def = Defs.Machines[id]
	if def.hidden or not Grid.isDir(dir) then
		return
	end
	if not groundAllows(island, def, x, y, z) then
		local names = {}
		for _, below in def.needsBelow do
			table.insert(names, Defs.name(below))
		end
		Net.get("Notify"):FireClient(
			player,
			def.name .. ": " .. table.concat(names, "이나 ") .. " 위에만 놓을 수 있습니다"
		)
		return
	end
	-- create() refuses if any cell of the footprint is taken or out of range
	if MachineService.create(island, id, x, y, z, dir, nil) then
		settle(island, cost)
	end
end

-- Creative mode: drops a few loose items of any kind into an empty cell.
local function drop(player: Player, id: any, x: any, y: any, z: any)
	local island = editable(player, x, y, z)
	if not island or not Defs.isItem(id) then
		return
	end
	local cell = island.cells[Grid.key(x, y, z)]
	if cell and (cell.kind == "block" or cell.machine.model:GetAttribute("Solid")) then
		return
	end
	-- Creative mode makes the items from nothing; otherwise they come out of the bag.
	local count = Config.DROP_COUNT
	if island.mode == "survival" then
		count = math.min(count, island.bag[id] or 0)
		if count < 1 or not Inventory.remove(island.bag, id, count) then
			return
		end
		Profile.push(island)
	end
	ItemService.spawn(id, count, IslandService.cellCenter(island, x, y, z))
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
	-- In survival mode a block has to be worked at: how long depends on the tool in the bag.
	-- Machines come up in one go, and in creative mode so does everything.
	if island.mode == "survival" and cell.kind == "block" then
		local needed = ToolLogic.blockHits(cell.id, island.bag)
		if needed > 1 then
			local swing, hits = ToolLogic.swing(swings[player], key, os.clock(), SWING_GAP, SWING_KEEP)
			swings[player] = swing
			if hits == 0 then
				return
			end
			Net.get("World"):FireClient(player, { kind = "progress", fraction = math.min(1, hits / needed) })
			if hits < needed then
				return
			end
		end
		swings[player] = nil
	end

	-- In survival mode what is broken goes back into the bag.
	local back: string? = nil
	if cell.kind == "machine" then
		back = Stock.machineReturn(cell.id)
		MachineService.remove(cell.machine, true)
	else
		back = Stock.blockDrop(cell.id, math.random())
		IslandService.clearCell(island, key)
	end
	if island.mode == "survival" and back then
		Inventory.add(island.bag, back, 1)
		Profile.push(island)
	end
end

local function pickup(player: Player)
	local island = IslandService.get(player)
	local position = rootPosition(player)
	if not island or not position or not allowed(player) then
		return
	end
	-- Only what lies on the player's own island can be picked up, so a visitor cannot walk off
	-- with what is lying on their host's.
	local part = ItemService.nearest(position, Config.PICKUP_RANGE)
	if not part or not IslandService.owns(island, part.Position) then
		return
	end
	local id, count = ItemService.info(part)
	if id then
		Inventory.add(island.bag, id, ItemService.take(part, count))
		Profile.push(island)
	end
end

function PlacementService.start()
	Net.get("Place").OnServerEvent:Connect(place)
	Net.get("Break").OnServerEvent:Connect(breakCell)
	Net.get("Drop").OnServerEvent:Connect(drop)
	Net.get("Pickup").OnServerEvent:Connect(pickup)
	Players.PlayerRemoving:Connect(function(player)
		swings[player] = nil
	end)
end

return PlacementService
