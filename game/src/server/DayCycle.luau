-- Moves the sun. One in-game day takes Config.DAY_MINUTES real minutes.
local Lighting = game:GetService("Lighting")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Config = require(ReplicatedStorage:WaitForChild("Shared").Config)

local DayCycle = {}

function DayCycle.start()
	local hoursPerSecond = 24 / (Config.DAY_MINUTES * 60)
	-- Once a second is smooth enough, and every change is sent to every player.
	local carried = 0
	RunService.Heartbeat:Connect(function(dt)
		carried += dt
		if carried >= 1 then
			Lighting.ClockTime = (Lighting.ClockTime + carried * hoursPerSecond) % 24
			carried = 0
		end
	end)
end

return DayCycle
