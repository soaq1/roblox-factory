-- The launcher: throws each item it is given in an arc, forward and up. How far is set by its
-- owner. Once thrown the item is an ordinary loose item in flight; nothing guides it.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace")
local Shared = ReplicatedStorage:WaitForChild("Shared")
local Config = require(Shared.Config)
local Defs = require(Shared.Defs)
local MoverLogic = require(Shared.MoverLogic)
local DeviceKit = require(script.Parent.Parent.DeviceKit)
local ItemService = require(script.Parent.Parent.ItemService)
local Kit = require(script.Parent.Parent.MachineKit)

local Launcher = {}

local RANGES = { 2, 3, 4, 5, 6 } -- cells from the launcher to where the item comes down
local ANGLE = math.rad(45)
local COOLDOWN = 0.6 -- seconds between throws

local function show(machine)
	DeviceKit.say(
		machine,
		if DeviceKit.unpowered(machine) then DeviceKit.NO_POWER else machine.range .. "칸 앞으로"
	)
end

function Launcher.build(machine)
	Kit.visual(machine.model, machine.base, machine.id)
	local body = Kit.body(machine)
	machine.ins = Kit.inputs(Kit.ports(machine))
	machine.held = nil
	machine.wait = 0
	machine.range = RANGES[2]
	machine.label = Kit.label(body, machine.def.height)
	machine.shown = ""
	show(machine)
	Kit.prompt(machine, body, "거리 바꾸기", function(player)
		Launcher.act(machine, player, "range", nil)
	end)
end

function Launcher.act(machine, player: Player, action: string, _arg: any)
	if action == "range" and DeviceKit.isOwner(machine, player) then
		local index = table.find(RANGES, machine.range) or 0
		machine.range = RANGES[index % #RANGES + 1]
		show(machine)
	end
end

function Launcher.load(machine, saved)
	if type(saved) ~= "table" then
		return
	end
	if table.find(RANGES, saved.range) then
		machine.range = saved.range
		show(machine)
	end
	if Defs.isItem(saved.held) then
		machine.held = saved.held
	end
end

function Launcher.save(machine)
	return { range = machine.range, held = machine.held }
end

function Launcher.accept(machine, id: string, _n: number): number
	if machine.held then
		return 0
	end
	machine.held = id
	return 1
end

function Launcher.tick(machine, dt: number)
	machine.busy = machine.held ~= nil -- an empty launcher draws no power
	show(machine)
	if DeviceKit.unpowered(machine) then
		return
	end
	machine.wait = math.max(0, machine.wait - dt)
	if not machine.held then
		machine.held = DeviceKit.pull(machine)
	end
	if not machine.held or machine.wait > 0 then
		return
	end
	-- Thrown from just above the launcher, aimed to come down on a belt at the launcher's own
	-- level the chosen number of cells ahead.
	local muzzle = Vector3.new(1.0, -Config.CELL / 2 + machine.def.height + 0.4, 0)
	local distance = machine.range * Config.CELL - muzzle.X
	local speed = MoverLogic.launchSpeed(distance, DeviceKit.RIDE - muzzle.Y, Workspace.Gravity, ANGLE)
	if not speed then
		return
	end
	local part = ItemService.spawn(machine.held, 1, (machine.base * CFrame.new(muzzle)).Position)
	if part then
		local throw = Vector3.new(math.cos(ANGLE) * speed, math.sin(ANGLE) * speed, 0)
		part.AssemblyLinearVelocity = machine.base:VectorToWorldSpace(throw)
	end
	machine.held = nil
	machine.wait = COOLDOWN
end

function Launcher.drops(machine): { [string]: number }
	return if machine.held then { [machine.held] = 1 } else {}
end

return Launcher
