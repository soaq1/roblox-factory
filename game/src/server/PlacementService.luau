-- Handles requests to place, break and pick up. Nothing a client sends is trusted:
-- every request is checked for type, range, ownership and rate before anything changes.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = require(Shared.Config)
local Defs = require(Shared.Defs)
local Grid = require(Shared.Grid)
local HandLogic = require(Shared.HandLogic)
local Inventory = require(Shared.Inventory)
local Net = require(Shared.Net)
local ToolLogic = require(Shared.ToolLogic)
local HandArm = require(script.Parent.HandArm)
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

-- Is anyone standing in this cell of the island? (Visitors count as much as the owner.)
local function someoneIn(island: IslandService.Island, x: number, y: number, z: number): boolean
	local center = IslandService.cellCenter(island, x, y, z)
	for _, other in Players:GetPlayers() do
		local at = rootPosition(other)
		if at and HandLogic.bodyInCell(center.X, center.Y, center.Z, Config.CELL, at.X, at.Y, at.Z) then
			return true
		end
	end
	return false
end

local function place(player: Player, id: any, x: any, y: any, z: any, dir: any)
	local island = editable(player, x, y, z)
	if not island or not Defs.isPlaceable(id) then
		return
	end
	HandArm.swing(player)
	local cost = payment(island, id)
	if cost == nil then
		Net.get("Notify"):FireClient(player, "가방에 " .. Defs.name(id) .. "이(가) 없습니다")
		return
	end
	if Defs.isBlock(id) then
		if someoneIn(island, x, y, z) then
			Profile.hint(player, "서 있는 자리에는 놓을 수 없습니다")
			return
		end
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

-- Lets go of one loose item. It lands in the cell the player aimed at if that is a free cell of
-- their own island within reach, and otherwise just in front of them. Things can only be put down
-- on the player's own island: left anywhere else, nobody could pick them up again.
local function drop(player: Player, id: any, x: any, y: any, z: any)
	local island = IslandService.get(player)
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	if not island or not root or not root:IsA("BasePart") or not Defs.isItem(id) or not allowed(player) then
		return
	end
	local at = (root.CFrame * CFrame.new(0, 0.5, -3.5)).Position
	if Grid.isInt(x) and Grid.isInt(y) and Grid.isInt(z) and Grid.inBounds(x, y, z, Config.MAX_COORD) then
		local center = IslandService.cellCenter(island, x, y, z)
		local cell = island.cells[Grid.key(x, y, z)]
		local solid = cell and (cell.kind == "block" or cell.machine.model:GetAttribute("Solid"))
		if not solid and (center - root.Position).Magnitude <= Config.REACH + Config.CELL then
			at = center
		end
	end
	if not IslandService.owns(island, at) then
		Profile.hint(player, "물건은 자기 섬에서만 내려놓을 수 있습니다")
		return
	end
	-- Nothing can be broken without a tool, so the last one is not let go of: without it there
	-- would be no way to get the wood for another.
	if island.mode == "survival" and ToolLogic.parse(id) and ToolLogic.count(island.bag) <= 1 then
		Profile.hint(player, "마지막 도구는 내려놓을 수 없습니다")
		return
	end
	-- Creative mode makes the item from nothing; otherwise it comes out of the bag.
	if island.mode == "survival" then
		if not Inventory.remove(island.bag, id, 1) then
			return
		end
		Profile.push(island)
	end
	ItemService.spawn(id, 1, at)
end

local function breakCell(player: Player, x: any, y: any, z: any)
	local island = editable(player, x, y, z)
	if not island then
		return
	end
	HandArm.swing(player)
	local key = Grid.key(x, y, z)
	local cell = island.cells[key]
	if not cell then
		return
	end
	-- Nothing is broken without a tool in the hand.
	local hand = Profile.inHand(island)
	if next(hand) == nil then
		Profile.hint(player, Profile.NEED_TOOL)
		return
	end
	if cell.kind == "block" and ToolLogic.spares(island.extra.held, cell.id) then
		return
	end
	-- A hoe does not break soil, it tills it: the block becomes farmland where it lies.
	if cell.kind == "block" and ToolLogic.tills(island.extra.held, cell.id) then
		IslandService.clearCell(island, key)
		IslandService.setBlock(island, x, y, z, "farmland")
		return
	end
	-- In survival mode a thing has to be worked at: how long depends on the tool in the hand.
	-- A block wants the tool for its material; a machine is lifted with a pickaxe. Every cell of a
	-- machine counts as the same target. In creative mode everything comes up in one go.
	if island.mode == "survival" then
		local needed, swingAt = 1, key
		if cell.kind == "block" then
			needed = ToolLogic.blockHits(cell.id, hand)
		else
			local target = cell.machine
			local hardness = if target.mod.hardness
				then target.mod.hardness(target)
				else ToolLogic.machineHardness(target.def)
			needed =
				ToolLogic.machineHits(hardness, hand, if target.def.behavior == "tree" then "axe" else "pick")
			swingAt = cell.machine.key
		end
		if needed > 1 then
			local swing, hits = ToolLogic.swing(swings[player], swingAt, os.clock(), SWING_GAP, SWING_KEEP)
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

	local changed = false
	local back: string? = nil
	if cell.kind == "machine" then
		-- What the machine held goes into the owner's bag with it, rather than spilling.
		local machine = cell.machine
		back = Stock.machineReturn(cell.id)
		if machine.mod.drops then
			local ok, held = pcall(machine.mod.drops, machine)
			if ok and type(held) == "table" then
				for id, count in held do
					if Inventory.add(island.bag, id, count) then
						changed = true
					end
				end
			end
		end
		MachineService.remove(machine, false)
	else
		back = Stock.blockDrop(cell.id, math.random())
		IslandService.clearCell(island, key)
	end
	-- In survival mode what is broken goes back into the bag.
	if island.mode == "survival" and back then
		Inventory.add(island.bag, back, 1)
		changed = true
	end
	if changed then
		Profile.push(island)
	end
end

-- Picks up one loose stack. The one the player is pointing at is taken if it is close enough;
-- otherwise the nearest one lying still, and items riding a belt only when nothing else is near.
local function pickup(player: Player, aimed: any, repeated: any)
	local island = IslandService.get(player)
	local position = rootPosition(player)
	if not island or not position or not allowed(player) then
		return
	end
	local part: BasePart? = nil
	if typeof(aimed) == "Instance" and aimed:IsA("BasePart") and ItemService.info(aimed) then
		if (aimed.Position - position).Magnitude <= Config.PICKUP_RANGE then
			part = aimed
		end
	end
	-- A key held down only gathers what lies still: it would otherwise strip a running belt.
	part = part or ItemService.pick(position, Config.PICKUP_RANGE, repeated == true)
	-- Only what lies on the player's own island can be picked up, so a visitor cannot walk off
	-- with what is lying on their host's.
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
	Net.get("Hold").OnServerEvent:Connect(function(player: Player, entry: any)
		local island = IslandService.get(player)
		if island and allowed(player) then
			Profile.hold(island, entry)
			HandArm.hold(player, entry)
		end
	end)
	Net.get("Pickup").OnServerEvent:Connect(pickup)
	Players.PlayerRemoving:Connect(function(player)
		swings[player] = nil
	end)
end

return PlacementService
