-- Raises the character's arm while the player is holding something, and swings it when they use it.
--
-- Roblox's own animation script already does both for any equipped Tool, so this keeps an empty,
-- unseen Tool in the character while the hand is not empty. The Tool has to be put there by the
-- server: one made on the client is never really equipped (Roblox does not weld its handle to the
-- hand, so no RightGrip appears) and Roblox takes it away again within a second or two. That is
-- why the arm kept dropping. Being on the server also means other players see the same arm.
--
-- What the player sees in their hand is a separate thing, drawn only on their own screen by
-- client/HandView.luau.
local Players = game:GetService("Players")

local HandArm = {}

-- Roblox's animation script holds the slash for about this long before letting the arm settle back.
-- Asking for another swing sooner restarts the slash from the beginning, which judders instead of
-- looking like repeated swinging. A held use sends a swing every 0.2 seconds and a drag every 0.05,
-- so the animation is spaced out here. How fast a block actually breaks is a separate matter and is
-- not touched by this.
local SWING_GAP = 0.3

-- Whether each player's hand is meant to be full, remembered so a new body gets the same arm.
local holding: { [Player]: boolean } = {}
local lastSwing: { [Player]: number } = {}

local function toolIn(character: Model): Tool?
	local tool = character:FindFirstChild("HeldArm")
	return if tool and tool:IsA("Tool") then tool else nil
end

-- Puts the empty Tool in the character, or takes it away. Safe to call with nothing changed.
local function apply(player: Player)
	local character = player.Character
	if not character or character.Parent == nil then
		return
	end
	local tool = toolIn(character)
	if holding[player] then
		if tool then
			return
		end
		local made = Instance.new("Tool")
		made.Name = "HeldArm"
		made.CanBeDropped = false
		made.ManualActivationOnly = true
		-- Roblox only counts a Tool as equipped once it has welded a part named Handle to the
		-- right hand, and the animation script only animates an equipped Tool.
		local handle = Instance.new("Part")
		handle.Name = "Handle"
		handle.Size = Vector3.new(0.2, 0.2, 0.2)
		handle.Transparency = 1
		handle.CanCollide = false
		handle.CanQuery = false
		handle.CanTouch = false
		handle.Massless = true
		handle.Parent = made
		made.Parent = character
	elseif tool then
		tool:Destroy()
	end
end

-- Call when what the player holds changes. Anything other than an empty hand counts as holding.
function HandArm.hold(player: Player, entry: any)
	holding[player] = type(entry) == "string" and entry ~= ""
	apply(player)
end

-- Call when the player uses what is in their hand. Roblox's animation script looks for a note
-- called "toolanim" on the held Tool, plays its slash once, and takes the note away again.
--
-- It takes it away on the machine it runs on, which is the player's own, so the server's copy of
-- the note stays where it is. Asking whether a note is already there and leaving it alone would
-- therefore swing once and never again -- that is exactly what happened. So the old note is thrown
-- away and a fresh one put in its place; the new child is what the animation script notices.
-- Returns the note it left, for the self-test to look at.
function HandArm.swing(player: Player): StringValue?
	local character = player.Character
	local tool = character and toolIn(character)
	if not tool then
		return nil
	end
	local now = os.clock()
	if now - (lastSwing[player] or -10) < SWING_GAP then
		return nil -- too soon: let the swing that is running play out
	end
	lastSwing[player] = now
	local old = tool:FindFirstChild("toolanim")
	if old then
		old:Destroy()
	end
	local note = Instance.new("StringValue")
	note.Name = "toolanim"
	note.Value = "Slash"
	note.Parent = tool
	return note
end

-- Whether the arm is up and Roblox accepted the Tool, for the self-test to report.
function HandArm.state(player: Player): { holding: boolean, tool: boolean, equipped: boolean }
	local character = player.Character
	local tool = character and toolIn(character)
	local hand = character and character:FindFirstChild("RightHand")
	return {
		holding = holding[player] == true,
		tool = tool ~= nil,
		equipped = hand ~= nil and hand:FindFirstChild("RightGrip") ~= nil,
	}
end

function HandArm.start()
	local function watch(player: Player)
		player.CharacterAdded:Connect(function()
			-- The body arrives empty-handed; give it back the arm the player had.
			task.defer(apply, player)
		end)
	end
	Players.PlayerAdded:Connect(watch)
	for _, player in Players:GetPlayers() do
		watch(player)
	end
	Players.PlayerRemoving:Connect(function(player)
		holding[player] = nil
		lastSwing[player] = nil
	end)
end

return HandArm
