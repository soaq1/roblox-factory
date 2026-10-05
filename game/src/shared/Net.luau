-- The channels the server and client talk over. The server creates them; the client waits for them.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local NAMES = {
	-- client to server
	"Place",
	"Break",
	"Pickup",
	"Drop",
	"Hold", -- which hotbar entry is in the hand
	"Craft",
	"Hand",
	"Upgrade",
	"TradeAct",
	"ShopAct", -- buy from or sell to a merchant
	"VisitAct", -- go to another player's island, or home
	"MachineAct", -- do something to a placed machine: owner id, cell x y z, action, argument
	"WorldAct", -- mine a node, hit a monster, use a portal
	-- server to client
	"Notify",
	"Bag",
	"State",
	"Trade",
	"Shop", -- a merchant's counter was opened
	"Visit", -- the list of islands that can be visited
	"MachineInfo", -- a placed machine wants its screen shown
	"World", -- mining progress, monster health and the like
}

local folder: Folder
if RunService:IsServer() then
	folder = Instance.new("Folder")
	folder.Name = "Remotes"
	for _, name in NAMES do
		local remote = Instance.new("RemoteEvent")
		remote.Name = name
		remote.Parent = folder
	end
	folder.Parent = ReplicatedStorage
else
	folder = ReplicatedStorage:WaitForChild("Remotes") :: Folder
end

local Net = {}

function Net.get(name: string): RemoteEvent
	return folder:WaitForChild(name) :: RemoteEvent
end

return Net
