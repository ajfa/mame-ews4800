-- Installs UX/4800 to disk, driving the installer menu.
--
--   EWS_KEYS  = "frame:text;frame:text;..."  what to type and when
--   EWS_SHOTS = "f1,f2,..."                   frames to dump the screen at
--
-- The screen dump goes to fvtags/fb<frame>.bin, 2 MB from physical
-- 0x10000000, which at 256 bytes per line and one bit per pixel is the console.
-- Convert it with fbpng.py.
local mac = manager.machine
if not mac.debugger then print("NO DEBUGGER") return end
local dbg = mac.debugger
local cpu = mac.devices[":cpu"]
local mem = cpu.spaces["program"]
local DIR = os.getenv("EWS_TAGDIR") or (os.getenv("HOME") .. "/ews4800/fvtags")
local BANKS = tonumber(os.getenv("EWS_BANKS") or "1")

dbg:command(string.format(
    "bpset a0900030,1,{trace %s/entry.log,0,noloop; " ..
    "tracelog \"IOPBOOT entry: v1=%%08X -> %d\\n\",v1; trace off; v1=%d; g}",
    DIR, BANKS, BANKS))
-- keyboard stages, to separate "the key never arrives" from "the installer ignores it"
local function mk(n) local f = io.open(DIR .. "/" .. n .. ".log", "w") if f then f:close() end end
mk("kb")
for _, b in ipairs({
    { "800210e8", "20 kbmsint" },
    { "800220b4", "21 kbmskbint" },
    { "80021ce0", "22 kbms_kbsoftint" },
}) do
    dbg:command(string.format(
        "bpset %s,1,{trace >>%s/kb.log,0,noloop; tracelog \"%s\\n\"; trace off; g}",
        b[1], DIR, b[2]))
end

-- Watchpoints (EWS_BZWATCH=1) on the two bcon softc fields that
-- decide the buzzer. The softc is static, bcon_vs at 0x802bcff8, measured:
--     gatype  softc[0x34]  virtual 0x802bd02c
--     buzzer  softc[0x64]  virtual 0x802bd05c
--
-- And they go by PHYSICAL address: the CPU map in ews4800.cpp is physical
-- (0x1e000000, 0x1fc00000, 0x10000000 and so on) and MAME MIPS3 translates BEFORE
-- reaching the bus, so a watchpoint never sees a 0x8 or 0xA address. KSEG0 and
-- KSEG1 are the SAME physical address here, and that is the only one that fires:
--     gatype  -> 0x2bd02c        buzzer -> 0x2bd05c
-- (Poner el watchpoint en 0x802bd05c fue el error de la tanda anterior: esa
-- nobody touches the physical one, so "it never fires" was a fault of the
-- instrument, not of the machine.)
--
-- They cost about 3x in speed because the field lives in main RAM and force
-- every write to be checked, so they are ARMED LATE: EWS_BZWATCH_AT, default
-- 9000, already measured with buzz=0, leaves the boot running at full speed.
mk("bz")
_G.bzwatch_at = tonumber(os.getenv("EWS_BZWATCH_AT") or "9000")
_G.bzwatch_on = os.getenv("EWS_BZWATCH") ~= "1"   -- true = ya no hay que armar

local function arm_bzwatch()
    -- wpset takes the CONDITION before the action:
    --      wpset <dir>,<long>,<tipo>[,<condicion>[,<accion>]]
    -- Sin el "1," de la condicion, MAME se come la accion COMO condicion y el
    -- the watchpoint is installed but silent, which is what used to happen.
    dbg:command("wpset 2bd02c,4,w,1,{trace >>" .. DIR ..
        "/bz.log,0,noloop; tracelog \"GATYPE  pc=%08X val=%08X\\n\",pc,wpdata; trace off; g}")
    dbg:command("wpset 2bd05c,4,w,1,{trace >>" .. DIR ..
        "/bz.log,0,noloop; tracelog \"BUZPTR  pc=%08X val=%08X\\n\",pc,wpdata; trace off; g}")
    local h = io.open(DIR .. "/bz.log", "a")
    if h then h:write(string.format("[armados en el frame %d]\n", _G.frames or 0)); h:close() end
end

-- EWS_BZTRAP=1: instead of waiting for someone to WRITE the field, watch
-- what the buzzer routine itself READS, exactly where it blows up.
--   80029904  lw t0,-31232(gp)   ; t0 = bcon (el puntero al softc)
--   80029908  lw t1,100(t0)      ; t1 = softc[0x64]  <- the one that reads FF000000
--   80029910  sh zero,0(t1)      ; fails here, in the delay slot
-- Registered through MEMORY EXPRESSIONS (d@, which the debugger treats as
-- virtual) rather than register names, so it does not depend on how MAME
-- names t0 and t1 on MIPS3. A breakpoint costs nothing until it fires.
if os.getenv("EWS_BZTRAP") == "1" then
    -- NOT NESTED: MAME misparses d@(d@X+N), it returned 0C0AB5F0 for gatype, which
    -- is a word of code). Since bcon is CONSTANT and already measured
    -- (0x802bcff8 = bcon_vs), the fields are read at literal addresses:
    --     softc+0x34 -> 802bd02c   softc+0x64 -> 802bd05c   softc+0x98 -> 802bd090
    mk("bztrap")
    dbg:command("bpset 80029904,1,{trace >>" .. DIR ..
        "/bztrap.log,0,noloop; tracelog \"VTBUZ  bcon=%08X gatype=%08X buzz=%08X s98=%08X\\n\"," ..
        "d@802a4e00,d@802bd02c,d@802bd05c,d@802bd090; trace off; g}")
    -- and the same field on the way out of bcon_buzinit, to see what it really set
    dbg:command("bpset 8002f310,1,{trace >>" .. DIR ..
        "/bztrap.log,0,noloop; tracelog \"BUZINIT bcon=%08X gatype=%08X buzz=%08X s98=%08X\\n\"," ..
        "d@802a4e00,d@802bd02c,d@802bd05c,d@802bd090; trace off; g}")
end

-- The SCSI tap USED TO BE HERE and was removed. install_write_tap
-- from Lua does not work on this machine: the r4000 space is 64 bit, the
-- first mask is 0xff00000000000000 and sol2 raises "integer value will be
-- misrepresented in lua" ANTES de llamar a la funcion, con lo que MAME se va
-- entero (segfault).  El registro de ordenes SCSI vive ahora en el driver,
-- en `ews4800.cpp` (scsi_r/scsi_w), y se enciende con EWS_SCSILOG=<ruta>.

dbg.execution_state = "run"

-- key script
local KEYS = {}
for item in (os.getenv("EWS_KEYS") or ""):gmatch("[^;]+") do
    local f, t = item:match("^(%d+):(.*)$")
    if f then KEYS[tonumber(f)] = t end
end
local SHOTS = {}
for f in (os.getenv("EWS_SHOTS") or ""):gmatch("%d+") do SHOTS[tonumber(f)] = true end

local FRAMES = tonumber(os.getenv("EWS_FRAMES") or "24000")
local STOPON = os.getenv("EWS_STOPON")
SHOTS[FRAMES] = true
local SAVEAT = tonumber(os.getenv("EWS_SAVEAT") or "") or nil
local SAVENAME = os.getenv("EWS_SAVENAME") or "step"

print("install armed")
for f, t in pairs(KEYS) do print(string.format("  key at %d: %q", f, t)) end

-- EWS_PCHIST=1: histograma del PC, una muestra por frame.  Es el instrumento
-- to find out WHERE the time goes when the machine advances but slowly:
-- 30000 frames (500 s emulados) por cada "part" de un paquete son ordenes de
-- orders of magnitude more than it would cost on the real machine, so either
-- espera del guest o algo del rig lo obliga a darlo.  Se resuelve fuera con
-- unixsyms.py --addr, que ya nombra las direcciones del kernel.
_G.pchist = {}
_G.pctotal, _G.pckern, _G.pcuser, _G.pcrom = 0, 0, 0, 0
_G.pchist_on = os.getenv("EWS_PCHIST") == "1"

_G.pchist_every = tonumber(os.getenv("EWS_PCHIST_EVERY") or "100000")

local function dump_pchist()
    local t = {}
    for pc, c in pairs(_G.pchist) do t[#t + 1] = { pc, c } end
    table.sort(t, function(a, b) return a[2] > b[2] end)
    local h = io.open(DIR .. "/pchist.log", "w")
    if not h then return end
    h:write(string.format("# frames %d muestras %d kernel %d usuario %d rom %d\n",
        _G.frames, _G.pctotal, _G.pckern, _G.pcuser, _G.pcrom))
    for i = 1, #t do
        h:write(string.format("%08x %d\n", t[i][1], t[i][2]))
    end
    h:close()
    print(string.format("[frame %d] histograma del PC: %d direcciones distintas",
          _G.frames, #t))
end

-- BOOTDEV (NVSRAM 0xbe493030): 0 FDD, 2 DISCO, 3 CD-ROM, 4 cinta, 6 red.
-- BOOTUNIT (0x3034) es el SCSI ID.
_G.bootdev = tonumber(os.getenv("EWS_BOOTDEV") or "3")
_G.bootid = tonumber(os.getenv("EWS_BOOTID") or os.getenv("EWS_CDID") or "0")

-- EWS_KEYFILE: the HOT key channel.
--
-- EWS_KEYS se fija al arrancar MAME, y eso dejo la instalacion colgada de un
-- `Choice ? [ yes no ]` que no se podia contestar: MAME con `-video none` no
-- answers neither SIGTERM nor SIGINT, so the only way out was to kill it. With
-- this, writing one line into the file from outside is enough.
_G.keyfile = os.getenv("EWS_KEYFILE")

local function poll_keyfile()
    local f = io.open(_G.keyfile, "r")
    if not f then return end
    local rest = {}
    local first = nil
    for line in f:lines() do
        if first == nil and line ~= "" then first = line else rest[#rest + 1] = line end
    end
    f:close()
    if not first then return end
    local w = io.open(_G.keyfile, "w")
    if w then
        for _, l in ipairs(rest) do w:write(l, "\n") end
        w:close()
    end
    -- `!shot [label]`: screen dump ON DEMAND. Dumps used to go at fixed frame
    -- fijos programados al arrancar, lo que deja ciego en cuanto se conduce una
    -- an interactive shell: you have to look AFTER each command, and there is no
    -- de antemano en que frame cae.
    if first:match("^!shot") then
        local tag = first:match("^!shot%s+(%S+)$") or ("d" .. tostring(_G.frames))
        local ok2, err2 = pcall(function() _G.shot(tag) end)
        print(string.format("[frame %d] captura %q: %s", _G.frames, tag,
              ok2 and "ok" or tostring(err2)))
        return
    end

    local port, field = first:match("^@([%w_]+)/(.+)$")
    local ok, err
    if port then
        ok, err = pcall(function()
            local fl = manager.machine.ioport.ports[":" .. port].fields[field]
            fl:set_value(1)
            _G.holding = fl
            _G.holduntil = _G.frames + 6
        end)
    else
        ok, err = pcall(function() manager.machine.natkeyboard:post_coded(first) end)
    end
    print(string.format("[frame %d] hot key %q: %s", _G.frames, first,
          ok and "ok" or tostring(err)))
end

_G.frames = 0
_G.seen = {}
_G.order = {}

local function sample_console()
    local out, line = {}, {}
    for n = 0, 1999 do
        local c = mem:read_u8(0x003080a8 + n)
        if c == 10 or c == 13 then
            if #line > 0 then out[#out + 1] = table.concat(line) end
            line = {}
        elseif c >= 32 and c < 127 then line[#line + 1] = string.char(c)
        end
    end
    if #line > 0 then out[#out + 1] = table.concat(line) end
    for _, s in ipairs(out) do
        if #s >= 4 and not _G.seen[s] then
            _G.seen[s] = _G.frames
            _G.order[#_G.order + 1] = s
            if STOPON and s:find(STOPON, 1, true) then
                _G.stop_now = s
            end
        end
    end
end

-- global a proposito: poll_keyfile se define ANTES y necesita llamarla
function _G.shot(tag)
    local f = io.open(string.format("%s/fb%s.bin", DIR, tag), "wb")
    if not f then return end
    local t = {}
    for off = 0, 0x1fffff, 4 do
        local ok, v = pcall(function() return mem:read_u32(0x10000000 + off) end)
        t[#t + 1] = string.pack(">I4", (ok and v) or 0)
    end
    f:write(table.concat(t))
    f:close()
    local nz = 0
    for off = 0, 0x1fffff, 64 do
        local ok, v = pcall(function() return mem:read_u32(0x10000000 + off) end)
        if ok and v and v ~= 0 then nz = nz + 1 end
    end
    print(string.format("[frame %s] screen dumped (%d lit samples)", tag, nz))
end

_G.h = function()
    _G.frames = _G.frames + 1
    mem:write_u8(0x1e493030, _G.bootdev)
    mem:write_u8(0x1e493034, _G.bootid)

    -- arm the buzzer watchpoints when the time comes
    if not _G.bzwatch_on and _G.frames >= _G.bzwatch_at then
        _G.bzwatch_on = true
        arm_bzwatch()
        print(string.format("[frame %d] watchpoints del zumbador armados", _G.frames))
    end

    -- EWS_BUZFIX repairs the kernel inconsistency that kills the machine
    -- as soon as the installer beeps, and it beeps on any error.
    --
    -- Measured on the machine, not assumed:
    --     BUZINIT  bcon=802BCFF8  gatype=00000000  buzz=00000000  s98=BE4A0050
    -- that is: for OUR machine class (14) the kernel installs the buzzer at
    -- softc[0x98] = 0xBE4A0050, pero `bcon_vtbuz` despacha por `gatype`, que se
    -- stays 0 because class 14 without a node never assigns it, and type 0
    -- reads softc[0x64], which NOBODY ever writes (the only kernel writer is
    -- bcon_buzinit+0x50, and only for classes 1 to 4). Result: garbage
    -- 0xFF000000 -> TLB fault -> PANIC.
    --
    -- softc[0x64] is given the address the kernel itself installed for
    -- this machine (0xBE4A0050, physical 0x3E4A0050, ALREADY MAPPED in ews4800.cpp
    -- No address is invented and gatype is not touched, so the
    -- dibujado de la consola sigue por el camino del tipo 0, que es el que
    -- works. It is a repair of the rig, not a claim about the hardware:
    -- root cause remains that we tell the kernel we are a /330.
    if os.getenv("EWS_BUZFIX") == "1" and _G.frames >= 9000
       and _G.frames % 200 == 0 then
        if mem:read_u32(0x002a4e00) == 0x802bcff8 then     -- bcon -> softc
            local s98 = mem:read_u32(0x002bd090)           -- softc[0x98]
            if s98 ~= 0 and mem:read_u32(0x002bd05c) ~= s98 then
                mem:write_u32(0x002bd05c, s98)             -- softc[0x64] = s98
                if not _G.buzfix_done then
                    _G.buzfix_done = true
                    print(string.format(
                        "[frame %d] zumbador reparado: softc[0x64] = %08X",
                        _G.frames, s98))
                end
            end
        end
    end

    -- The PC is read as TEXT, not through .value.
    --
    -- cpu.state["PC"].value returns the 64 bit PC, and for any kernel or ROM
    -- address that is 0xFFFFFFFF8........, which does NOT fit in
    -- el entero con signo de Lua**: sol2 lanza (el mismo
    -- "integer value will be misrepresented in lua" que tumba los grifos) y el
    -- pcall se traga la muestra. Solo sobreviven las direcciones de usuario,
    -- que son 0x00000000004....., pequenas y positivas.
    --
    -- O sea que el histograma "100% en espacio de usuario" de la primera medida
    -- NO era una medida: era el instrumento descartando en silencio todo lo que
    -- pasaba en el kernel. `tostring()` formatea sin convertir y no falla nunca.
    if _G.pchist_on then
        local ok, hex = pcall(function() return tostring(cpu.state["PC"]) end)
        local v = ok and hex and tonumber(hex:sub(-8), 16)
        if v then
            local pc = v & 0xffffffff
            local pg = pc & 0xfffff000
            _G.pchist[pg] = (_G.pchist[pg] or 0) + 1
            _G.pctotal = _G.pctotal + 1
            if pc >= 0xbfc00000 then
                _G.pcrom = _G.pcrom + 1
            elseif pc >= 0x80000000 then
                _G.pckern = _G.pckern + 1
            else
                _G.pcuser = _G.pcuser + 1
            end
        end
    end

    if _G.pchist_on and _G.frames % _G.pchist_every == 0 then dump_pchist() end

    if _G.keyfile and _G.frames % 30 == 0 then poll_keyfile() end

    if _G.frames % 50 == 0 then sample_console() end

    -- release a function key pressed six frames earlier
    if _G.holding and _G.frames == _G.holduntil then
        pcall(function() _G.holding:set_value(0) end)
        _G.holding = nil
    end

    local k = KEYS[_G.frames]
    if k then
        -- "@port/field" presses an ioport field (function keys have no
        -- character, so they cannot go through the natural keyboard)
        local port, field = k:match("^@([%w_]+)/(.+)$")
        if port then
            local ok, err = pcall(function()
                local f = mac.ioport.ports[":" .. port].fields[field]
                f:set_value(1)
                _G.holding = f
                _G.holduntil = _G.frames + 6
            end)
            print(string.format("[frame %d] pulsada %s/%s: %s", _G.frames, port, field,
                  ok and "ok" or tostring(err)))
        else
            local ok, err = pcall(function() mac.natkeyboard:post_coded(k) end)
            print(string.format("[frame %d] tecleado %q: %s", _G.frames, k,
                  ok and "ok" or tostring(err)))
        end
    end

    if SHOTS[_G.frames] then shot(tostring(_G.frames)) end

    -- save state so that each step does not repeat 20 minutes of booting
    if SAVEAT and _G.frames == SAVEAT then
        local ok, err = pcall(function() mac:save(SAVENAME) end)
        print(string.format("[frame %d] estado guardado en %q: %s", _G.frames,
              SAVENAME, ok and "ok" or tostring(err)))
    end

    if _G.stop_now then
        print(string.format("[frame %d] the console said %q: stopping here",
              _G.frames, _G.stop_now))
        shot("stop" .. tostring(_G.frames))
        _G.stop_now = nil
        _G.forced_end = true
    end

    if _G.frames == FRAMES or _G.forced_end then
        sample_console()
        print("=== CONSOLA DEL KERNEL")
        for _, s in ipairs(_G.order) do
            print(string.format("  [%6d] %s", _G.seen[s], s))
        end
        if _G.pchist_on then dump_pchist() end
        print("PC=" .. tostring(cpu.state["PC"]))
        mac:exit()
    end
end
_G.sub = emu.add_machine_frame_notifier(_G.h)
