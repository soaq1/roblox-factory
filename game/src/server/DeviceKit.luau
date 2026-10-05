-- Pieces shared by the devices: movers, farm machines and signal devices.
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = require(Shared.Config)
local Grid = require(Shared.Grid)
local ItemService = require(script.Parent.ItemService)
local Kit = require(script.Parent.MachineKit)

local DeviceKit = {}

local CELL = Config.CELL
local LIT = Color3.fromRGB(120, 220, 140)
local UNLIT = Color3.fromRGB(62, 64, 66)

-- Height of a belt's surface and of an item riding it, in a machine's own frame.
DeviceKit.BELT_TOP = -0.7
DeviceKit.RIDE = -0.45

DeviceKit.NO_POWER = "전기 없음"

-- True while a machine that needs electricity has none. The power system sets `powered` on every
-- machine that needs it; such a machine does nothing until it is true.
function DeviceKit.unpowered(machine): boolean
	return machine.def.needsPower == true and machine.powered ~= true
end

-- Shows text on a machine's read-out, touching the label only when the text changes.
function DeviceKit.say(machine, text: string)
	if machine.label and machine.shown ~= text then
		machine.shown = text
		machine.label.Text = text
	end
end

function DeviceKit.isOwner(machine, player: Player): boolean
	return machine.island.owner == player
end

-- The working parts of a straight belt, unseen, for devices whose catalogue model already draws a
-- belt: a surface that carries items forward and the two side rails. Returns the surface.
function DeviceKit.bed(machine): Part
	local model, base = machine.model, machine.base
	local parts = {
		Kit.part(model, base, Vector3.new(3, 0.6, 3), Vector3.new(0, -1.2, 0), Kit.COLORS.dark),
		Kit.part(model, base, Vector3.new(3, 0.6, 0.25), Vector3.new(0, -0.6, -1.3), Kit.COLORS.light),
		Kit.part(model, base, Vector3.new(3, 0.6, 0.25), Vector3.new(0, -0.6, 1.3), Kit.COLORS.light),
	}
	local surface = Kit.conveyor(
		model,
		base,
		Vector3.new(3, 0.2, 2.35),
		Vector3.new(0, -0.8, 0),
		Vector3.new(Config.BELT_SPEED, 0, 0)
	)
	table.insert(parts, surface)
	for _, part in parts do
		part.Transparency = 1
	end
	return surface
end

-- The loose items riding a device's belt.
function DeviceKit.onBed(machine): { BasePart }
	return ItemService.inBox(machine.base * CFrame.new(0, -0.2, 0), Vector3.new(2.9, 1.0, 2.2))
end

-- Takes one item from the machine's inputs, each input in turn so a busy one cannot starve the
-- rest. `wanted` can refuse kinds of item. Returns what was taken.
function DeviceKit.pull(machine, wanted: ((string) -> boolean)?): string?
	local count = #machine.ins
	for step = 0, count - 1 do
		local index = ((machine.nextIn or 1) - 1 + step) % count + 1
		local input = machine.ins[index]
		for _, part in ItemService.inBox(input.box, input.size) do
			local id = ItemService.info(part)
			if id and (not wanted or wanted(id)) and ItemService.take(part, 1) == 1 then
				machine.nextIn = index % count + 1
				return id
			end
		end
	end
	return nil
end

-- A mouth that is not in the catalogue data: `edge` is the middle of the mouth on the machine's
-- face and `outward` the way out of it, both in the machine's own frame.
function DeviceKit.mouth(machine, kind: string, edge: Vector3, outward: Vector3): Kit.Port
	local alongX = math.abs(outward.X) > 0.5
	local depth = if kind == "in" then 0.3 else 0.9
	return {
		kind = kind,
		box = machine.base * CFrame.new(edge + outward * (depth / 2) + Vector3.new(0, -0.55, 0)),
		size = if alongX then Vector3.new(depth, 1.9, 2.2) else Vector3.new(2.2, 1.9, depth),
		spawn = (machine.base * CFrame.new(edge + outward * 0.75 + Vector3.new(0, -0.15, 0))).Position,
	}
end

-- A space on top of a machine: whatever comes to rest there is taken in.
function DeviceKit.top(machine): Kit.Port
	return {
		kind = "in",
		box = machine.base * CFrame.new(0, -CELL / 2 + machine.def.height + 0.3, 0),
		size = Vector3.new(2.4, 1.0, 2.4),
		spawn = Vector3.zero,
	}
end

-- A small light showing whether something is on.
function DeviceKit.lamp(machine, offset: Vector3, size: Vector3, round: boolean?): Part
	local part = Kit.detail(machine.model, machine.base, size, offset, UNLIT)
	part.Name = "Lamp"
	if round then
		part.Shape = Enum.PartType.Ball
	end
	return part
end

function DeviceKit.setLamp(part: Part, on: boolean)
	part.Color = if on then LIT else UNLIT
	part.Material = if on then Enum.Material.Neon else Enum.Material.SmoothPlastic
end

-- What stands in a cell of the machine's island: the block's id, or nil.
function DeviceKit.blockAt(island, x: number, y: number, z: number): string?
	local cell = island.cells[Grid.key(x, y, z)]
	return if cell and cell.kind == "block" then cell.id else nil
end

function DeviceKit.machineAt(island, x: number, y: number, z: number): any?
	local cell = island.cells[Grid.key(x, y, z)]
	return if cell and cell.kind == "machine" then cell.machine else nil
end

function DeviceKit.isFree(island, x: number, y: number, z: number): boolean
	return island.cells[Grid.key(x, y, z)] == nil and Grid.inBounds(x, y, z, Config.MAX_COORD)
end

-- Every other machine touching this one: in the six cells around each cell it keeps.
function DeviceKit.touching(machine): { any }
	local found, seen = {}, {}
	local cells = machine.island.cells
	for _, key in machine.keys do
		local x, y, z = Grid.parseKey(key)
		if x and y and z then
			for _, step in { { 1, 0, 0 }, { -1, 0, 0 }, { 0, 1, 0 }, { 0, -1, 0 }, { 0, 0, 1 }, { 0, 0, -1 } } do
				local cell = cells[Grid.key(x + step[1], y + step[2], z + step[3])]
				if cell and cell.kind == "machine" and cell.machine ~= machine and not seen[cell.machine] then
					seen[cell.machine] = true
					table.insert(found, cell.machine)
				end
			end
		end
	end
	return found
end

-- Runs `visit` for every machine standing within `radius` cells of this one, on its own level
-- or one above or below.
function DeviceKit.eachNear(machine, radius: number, visit: (any) -> ())
	local seen = {}
	for dx = -radius, radius do
		for dz = -radius, radius do
			for dy = -1, 1 do
				local other =
					DeviceKit.machineAt(machine.island, machine.x + dx, machine.y + dy, machine.z + dz)
				if other and other ~= machine and not seen[other] then
					seen[other] = true
					visit(other)
				end
			end
		end
	end
end

return DeviceKit
