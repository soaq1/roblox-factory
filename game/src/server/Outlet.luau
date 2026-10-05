-- How a finished item leaves a machine. Normally it drops just outside the mouth, onto a belt or the
-- ground. When another machine stands right against the mouth there is no room to drop anything,
-- so the item is handed straight over if that machine has an input facing this way.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = require(Shared.Config)
local Grid = require(Shared.Grid)
local ItemService = require(script.Parent.ItemService)

local Outlet = {}

local CELL = Config.CELL
local FACING = 1.5 -- studs between this mouth's drop point and a neighbour's input for them to count as joined

local function facingInput(other, port): boolean
	for _, input in other.ins or {} do
		if (input.box.Position - port.spawn).Magnitude < FACING then
			return true
		end
	end
	return false
end

-- The cell just outside a mouth: what is there, if anything ({ kind = "block" | "machine", ... }).
function Outlet.facing(machine, port)
	local island = machine.island
	local origin = island.origin
	return island.cells[Grid.key(
		Grid.toCell(port.spawn.X, origin.X, CELL),
		Grid.toCell(port.spawn.Y, origin.Y, CELL),
		Grid.toCell(port.spawn.Z, origin.Z, CELL)
	)]
end

-- Is there a belt or a machine at this mouth for things to go to?
function Outlet.hasTaker(machine, port): boolean
	local cell = Outlet.facing(machine, port)
	return cell ~= nil and cell.kind == "machine" and cell.machine ~= machine
end

-- Tries to put one item out through a port. Returns true if it left the machine.
function Outlet.emit(machine, port, id: string): boolean
	local island = machine.island
	local origin = island.origin
	local key = Grid.key(
		Grid.toCell(port.spawn.X, origin.X, CELL),
		Grid.toCell(port.spawn.Y, origin.Y, CELL),
		Grid.toCell(port.spawn.Z, origin.Z, CELL)
	)
	local cell = island.cells[key]
	if cell then
		if cell.kind == "block" then
			return false
		end
		local other = cell.machine
		if other ~= machine and other.model:GetAttribute("Solid") and not other.def.walkThrough then
			if other.mod.accept and facingInput(other, port) then
				return other.mod.accept(other, id, 1) == 1
			end
			return false
		end
	end
	-- Wait while the last item is still sitting at the mouth, so a blocked line backs up instead of piling.
	if #ItemService.inBox(port.box, port.size) > 0 then
		return false
	end
	return ItemService.spawn(id, 1, port.spawn) ~= nil
end

return Outlet
