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

local machines: { [any]: boolean } = {}
local total = 0

local function moduleFor(name: string)
	return require(script.Parent.machines:FindFirstChild(name) :: ModuleScript) :: any
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
	local key = Grid.key(x, y, z)
	if not def or island.cells[key] then
		return nil
	end
	local model = Instance.new("Model")
	model.Name = id
	model:SetAttribute("Machine", id)
	model:SetAttribute("CellX", x)
	model:SetAttribute("CellY", y)
	model:SetAttribute("CellZ", z)

	local machine = {
		id = id,
		def = def,
		mod = moduleFor(def.module),
		island = island,
		key = key,
		x = x,
		y = y,
		z = z,
		dir = dir,
		model = model,
		center = IslandService.cellCenter(island, x, y, z),
		base = Kit.base(IslandService.cellCenter(island, x, y, z), dir),
	}
	machine.mod.build(machine)
	if machine.mod.load and saved ~= nil then
		machine.mod.load(machine, saved)
	end
	model.Parent = island.machinesFolder

	machines[machine] = true
	total += 1
	island.cells[key] = { kind = "machine", id = id, machine = machine }
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
	machine.island.cells[machine.key] = nil
	machine.model:Destroy()
end

function MachineService.removeIsland(island: IslandService.Island)
	for machine in machines do
		if machine.island == island then
			MachineService.remove(machine, false)
		end
	end
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
		for machine in machines do
			local tick = machine.mod.tick
			if tick then
				local ok, err = pcall(tick, machine, step)
				if not ok then
					warn("machine " .. machine.id .. " at " .. machine.key .. " failed: " .. tostring(err))
				end
			end
		end
	end)
end

return MachineService
