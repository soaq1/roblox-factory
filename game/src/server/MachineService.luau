-- Keeps track of every placed machine and runs each one on a fixed beat.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = require(Shared.Config)
local Defs = require(Shared.Defs)
local Grid = require(Shared.Grid)
local IslandService = require(script.Parent.IslandService)
local ItemService = require(script.Parent.ItemService)
local Kit = require(script.Parent.MachineKit)

local MachineService = {}

-- Which file in server/machines runs each kind of behaviour.
local MODULES = {
	belt = "Belt",
	extractor = "Extractor",
	processor = "Processor",
	passthrough = "Passthrough",
	chest = "Chest",
	sapling = "Plant",
	crop = "Plant",
	bench = "Bench",
	decor = "Decor",
	-- moving things about
	ramp = "Ramp",
	chute = "Chute",
	lift = "Lift",
	launcher = "Launcher",
	pusher = "Pusher",
	blower = "Blower",
	sorter = "Sorter",
	-- making and growing
	assembler = "Assembler",
	logger = "Logger",
	harvester = "Harvester",
	seeder = "Seeder",
	sprinkler = "Sprinkler",
	-- signals, power, trade
	signal = "Signal",
	power = "Power",
	vending = "Vending",
}

local machines: { [any]: boolean } = {}
local total = 0

local function moduleFor(behavior: string)
	local source = script.Parent.machines:FindFirstChild(MODULES[behavior] or "Decor")
	if not source then
		-- Not written yet: the machine can still be placed and looked at.
		source = script.Parent.machines:FindFirstChild("Decor")
	end
	return require(source :: ModuleScript) :: any
end

-- The keys of every cell a machine would cover, or nil if any of them is taken or out of range.
function MachineService.freeCells(
	island: IslandService.Island,
	id: string,
	x: number,
	y: number,
	z: number,
	dir: number
): { string }?
	local def = Defs.Machines[id]
	if not def then
		return nil
	end
	-- The anchor cell comes first; tall machines also keep the cells above them.
	local keys = {}
	for layer = 0, def.sy - 1 do
		for _, cell in Grid.footprint(x, z, dir, def.sx, def.sz) do
			if not Grid.inBounds(cell[1], y + layer, cell[2], Config.MAX_COORD) then
				return nil
			end
			local key = Grid.key(cell[1], y + layer, cell[2])
			if island.cells[key] then
				return nil
			end
			table.insert(keys, key)
		end
	end
	return keys
end

function MachineService.create(
	island: IslandService.Island,
	id: string,
	x: number,
	y: number,
	z: number,
	dir: number,
	saved: any?
)
	local def = Defs.Machines[id]
	local keys = MachineService.freeCells(island, id, x, y, z, dir)
	if not def or not keys then
		return nil
	end
	local model = Instance.new("Model")
	model.Name = id
	model:SetAttribute("Machine", id)
	model:SetAttribute("CellX", x)
	model:SetAttribute("CellY", y)
	model:SetAttribute("CellZ", z)

	local cx, cz = Grid.footprintCentre(dir, def.sx, def.sz)
	local center = IslandService.cellCenter(island, x, y, z)
		+ Vector3.new(cx * Config.CELL, 0, cz * Config.CELL)
	local machine = {
		id = id,
		def = def,
		mod = moduleFor(def.behavior),
		island = island,
		key = Grid.key(x, y, z),
		keys = keys,
		x = x,
		y = y,
		z = z,
		dir = dir,
		model = model,
		center = center,
		base = Kit.base(center, dir),
	}
	-- Parent first: a conveyor's velocity is only reliable once the part is in the world.
	model.Parent = island.machinesFolder
	local built, problem = pcall(function()
		machine.mod.build(machine)
		if machine.mod.load and saved ~= nil then
			machine.mod.load(machine, saved)
		end
	end)
	if not built then
		warn("could not build " .. id .. " at " .. machine.key .. ": " .. tostring(problem))
		model:Destroy()
		return nil
	end

	machines[machine] = true
	total += 1
	for _, key in keys do
		island.cells[key] = { kind = "machine", id = id, machine = machine }
	end
	return machine
end

function MachineService.remove(machine, dropContents: boolean)
	if not machines[machine] then
		return
	end
	machines[machine] = nil
	total -= 1
	if dropContents and machine.mod.drops then
		for id, count in machine.mod.drops(machine) do
			if count > 0 then
				ItemService.spawnMany(id, count, machine.center + Vector3.new(0, 1, 0))
			end
		end
	end
	for _, key in machine.keys do
		machine.island.cells[key] = nil
	end
	machine.model:Destroy()
end

function MachineService.removeIsland(island: IslandService.Island)
	for machine in machines do
		if machine.island == island then
			MachineService.remove(machine, false)
		end
	end
end

-- The machine covering a cell, if any.
function MachineService.at(island: IslandService.Island, x: number, y: number, z: number): any?
	local cell = island.cells[Grid.key(x, y, z)]
	return if cell and cell.kind == "machine" then cell.machine else nil
end

function MachineService.onIsland(island: IslandService.Island): { any }
	local list = {}
	for machine in machines do
		if machine.island == island then
			table.insert(list, machine)
		end
	end
	return list
end

function MachineService.saveState(machine): any?
	if machine.mod.save then
		return machine.mod.save(machine)
	end
	return nil
end

function MachineService.count(): number
	return total
end

function MachineService.start()
	local carried = 0
	RunService.Heartbeat:Connect(function(dt)
		carried += dt
		if carried < Config.MACHINE_TICK then
			return
		end
		-- After a long stall, run one beat rather than trying to catch up all at once.
		local step = math.min(carried, Config.MACHINE_TICK * 3)
		carried = 0
		local finished = {}
		for machine in machines do
			local tick = machine.mod.tick
			-- `halted` is set by signal devices to stop a neighbour; `powered` by the power system.
			if tick and not machine.halted then
				local ok, result = pcall(tick, machine, step)
				if not ok then
					warn("machine " .. machine.id .. " at " .. machine.key .. " failed: " .. tostring(result))
				elseif result == true then
					table.insert(finished, machine)
				end
			end
		end
		-- A machine that says it is done (a sapling that has grown) is removed, then gets to leave
		-- something behind.
		for _, machine in finished do
			MachineService.remove(machine, false)
			if machine.mod.finish then
				local ok, err = pcall(machine.mod.finish, machine)
				if not ok then
					warn("machine " .. machine.id .. " could not finish: " .. tostring(err))
				end
			end
		end
	end)
end

return MachineService
