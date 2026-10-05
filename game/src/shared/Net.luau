-- The channels the server and client talk over. The server creates them; the client waits for them.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local NAMES = { "Place", "Break", "Pickup", "Notify", "Bag" }

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
