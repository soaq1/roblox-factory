-- Plays the game's sounds on this player's own machine. A sound with no asset chosen yet
-- (id 0 in shared/Sounds) is skipped, so everything works in silence until the table is filled.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local SoundService = game:GetService("SoundService")

local Sounds = require(ReplicatedStorage:WaitForChild("Shared"):WaitForChild("Sounds"))

local SoundPlayer = {}

local made: { [string]: Sound } = {}

local function soundFor(name: string): Sound?
	local def = Sounds[name]
	if not def or def.id == 0 then
		return nil
	end
	local sound = made[name]
	if not sound then
		sound = Instance.new("Sound")
		sound.Name = name
		sound.SoundId = "rbxassetid://" .. def.id
		sound.Volume = def.volume
		sound.Parent = SoundService
		made[name] = sound
	end
	return sound
end

function SoundPlayer.play(name: string)
	local sound = soundFor(name)
	if not sound then
		return
	end
	local spread = Sounds[name].pitch
	sound.PlaybackSpeed = 1 + (math.random() * 2 - 1) * spread
	-- PlayLocalSound lets the same sound overlap itself, which fast swings need.
	SoundService:PlayLocalSound(sound)
end

-- The sound of striking a block, by what the block is made of.
local MATERIAL = {
	log = "hit_wood",
	planks = "hit_wood",
	grass = "hit_dirt",
	dirt = "hit_dirt",
	farmland = "hit_dirt",
	sand = "hit_dirt",
	gravel = "hit_dirt",
	clay = "hit_dirt",
	leaves = "hit_dirt",
}

function SoundPlayer.hit(blockId: string?)
	if not blockId then
		SoundPlayer.play("hit_other")
	else
		SoundPlayer.play(MATERIAL[blockId] or "hit_stone")
	end
end

return SoundPlayer
