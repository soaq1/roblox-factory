-- Moves the sun. One in-game day takes Config.DAY_MINUTES real minutes.
local Lighting = game:GetService("Lighting")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local Config = require(ReplicatedStorage:WaitForChild("Shared").Config)

local DayCycle = {}

function DayCycle.start()
	local hoursPerSecond = 24 / (Config.DAY_MINUTES * 60)
	RunService.Heartbeat:Connect(function(dt)
		Lighting.ClockTime = (Lighting.ClockTime + dt * hoursPerSecond) % 24
	end)
end

return DayCycle
