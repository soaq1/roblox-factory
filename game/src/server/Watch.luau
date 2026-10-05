-- Keeps a machine's window current while a player has it open. A machine's module opens the
-- window with Watch.open, calls Watch.push whenever what the window shows may have changed, and
-- closes it when the player says so. A player who has walked away or left is dropped quietly.
local HttpService = game:GetService("HttpService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Config = require(ReplicatedStorage:WaitForChild("Shared").Config)
local MachineActs = require(script.Parent.MachineActs)

local Watch = {}

local TOO_FAR = Config.REACH + 6 -- a little beyond acting range, so the edge does not flicker

function Watch.any(machine): boolean
	return machine.watchers ~= nil and next(machine.watchers) ~= nil
end

-- Shows `kind` of window to the player and remembers to keep it current.
function Watch.open(machine, player: Player, kind: string, info: { [string]: any })
	machine.watchers = machine.watchers or {}
	machine.watchers[player] = true
	machine.watchKind = kind
	MachineActs.show(player, machine, kind, info)
end

function Watch.close(machine, player: Player)
	if machine.watchers then
		machine.watchers[player] = nil
	end
end

local function stillThere(machine, player: Player): boolean
	local character = player.Character
	local root = character and character:FindFirstChild("HumanoidRootPart")
	if not player.Parent or not root or not root:IsA("BasePart") then
		return false
	end
	return (machine.center - root.Position).Magnitude <= TOO_FAR
end

-- Sends the window's contents again to everyone watching, if they have changed since last time
-- (or regardless, with `force`). `makeInfo` is only called when somebody is watching.
function Watch.push(machine, makeInfo: () -> { [string]: any }, force: boolean?)
	if not Watch.any(machine) then
		return
	end
	local info = makeInfo()
	local signature = HttpService:JSONEncode(info)
	if not force and signature == machine.watchSig then
		return
	end
	machine.watchSig = signature
	info.update = true -- tells the client not to reopen a window the player has just closed
	for player in machine.watchers do
		if stillThere(machine, player) then
			MachineActs.show(player, machine, machine.watchKind, info)
		else
			machine.watchers[player] = nil
		end
	end
end

return Watch
