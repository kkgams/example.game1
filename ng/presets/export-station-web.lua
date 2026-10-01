local pack_byte_count = inputs[1]
local output_dir = inputs[2]
local index_source = inputs[3]
local bridge_source = inputs[4]
local wasm_source = inputs[5]
local pack_source = inputs[6]

if type(pack_byte_count) ~= "number" or pack_byte_count <= 0 then
	error("Station Web Export requires a successfully generated content pack")
end
for label, value in pairs({
	["output directory"] = output_dir,
	["index source"] = index_source,
	["GL bridge source"] = bridge_source,
	["WASM source"] = wasm_source,
	["content pack source"] = pack_source,
}) do
	if type(value) ~= "string" or value == "" then
		error("Station Web Export requires " .. label)
	end
end

local index_html = host.call("fs/fs::read-text", index_source)
local gl_bridge = host.call("fs/fs::read-text", bridge_source)
local wasm = host.call("fs/fs::read-file", wasm_source)
local pack = host.call("fs/fs::read-file", pack_source)
if type(index_html) ~= "string" or index_html == "" then error("prebuilt index.html is empty") end
if type(gl_bridge) ~= "string" or gl_bridge == "" then error("prebuilt gl-bridge.js is empty") end
if type(wasm) ~= "table" or #wasm < 8 then error("prebuilt station-demo.wasm is invalid") end
if wasm[1] ~= 0 or wasm[2] ~= 97 or wasm[3] ~= 115 or wasm[4] ~= 109 then
	error("prebuilt station-demo.wasm has invalid magic")
end
if type(pack) ~= "table" or #pack ~= pack_byte_count then
	error("generated station.rspk byte count does not match respack output")
end
if pack[1] ~= 82 or pack[2] ~= 83 or pack[3] ~= 80 or pack[4] ~= 75 then
	error("generated station.rspk has invalid magic")
end

-- Licensing travels with every visitor export, not only the release ZIP.
-- Read all required legal/support bytes before changing output files.
local documents = {
	{"LICENSE", "LICENSE"},
	{"NOTICE", "NOTICE"},
	{"THIRD-PARTY-NOTICES.txt", "THIRD-PARTY-NOTICES.txt"},
	{"README.md", "BROWSER-README.md"},
}
for _, document in ipairs(documents) do
	document[3] = host.call("fs/fs::read-text", document[2])
	if type(document[3]) ~= "string" or document[3] == "" then
		error("required export document is empty: " .. document[2])
	end
end

local current = ""
for part in string.gmatch(output_dir, "[^/]+") do
	current = current == "" and part or (current .. "/" .. part)
	local created, create_error = pcall(host.call, "fs/fs::create-dir", current)
	if not created then
		local stat_ok, stat = pcall(host.call, "fs/fs::stat", current)
		if not stat_ok or type(stat) ~= "table" or stat.type ~= "directory" then
			error("cannot create export directory " .. current .. ": " .. tostring(create_error))
		end
	end
end

-- Validate every input before writing. The generated pack is written last, so
-- an interrupted static-file copy cannot advertise new content with an old
-- or partial pack.
host.call("fs/fs::write-text", output_dir .. "/index.html", index_html)
host.call("fs/fs::write-text", output_dir .. "/gl-bridge.js", gl_bridge)
host.call("fs/fs::write-file", output_dir .. "/station-demo.wasm", wasm)
for _, document in ipairs(documents) do
	host.call("fs/fs::write-text", output_dir .. "/" .. document[1], document[3])
end
host.call("fs/fs::write-file", output_dir .. "/station.rspk", pack)

outputs[1] = {
	directory = output_dir,
	files = {"index.html", "gl-bridge.js", "station-demo.wasm", "station.rspk", "LICENSE", "NOTICE", "THIRD-PARTY-NOTICES.txt", "README.md"},
	content_bytes = #pack,
	wasm_bytes = #wasm,
}
