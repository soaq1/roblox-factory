-- A small allowance per player that refills over time. Requests beyond it are dropped.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Config = require(ReplicatedStorage:WaitForChild("Shared").Config)

local RateLimit = {}

local buckets: { [Player]: { tokens: number, at: number } } = {}

function RateLimit.allow(player: Player): boolean
	local now = os.clock()
	local bucket = buckets[player]
	if not bucket then
		bucket = { tokens = Config.RATE_PER_SECOND, at = now }
		buckets[player] = bucket
	end
	bucket.tokens =
		math.min(Config.RATE_PER_SECOND, bucket.tokens + (now - bucket.at) * Config.RATE_PER_SECOND)
	bucket.at = now
	if bucket.tokens < 1 then
		return false
	end
	bucket.tokens -= 1
	return true
end

Players.PlayerRemoving:Connect(function(player)
	buckets[player] = nil
end)

return RateLimit
