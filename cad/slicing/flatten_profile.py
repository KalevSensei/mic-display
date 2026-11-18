import sys, re, io
src, out = sys.argv[1], sys.argv[2]
sel = {'printer': sys.argv[3], 'print': sys.argv[4], 'filament': sys.argv[5]}
secs = {}; cur = None
for line in io.open(src, encoding='utf-8'):
    line = line.rstrip('\n')
    m = re.match(r'^\[(\w+):(.+)\]\s*$', line)
    if m: cur = (m.group(1), m.group(2)); secs[cur] = {}; continue
    if line.startswith('[') : cur = None; continue
    if cur and '=' in line and not line.lstrip().startswith('#'):
        k, v = line.split('=', 1); secs[cur][k.strip()] = v.strip()
def resolve(kind, name, depth=0):
    d = secs[(kind, name)]; res = {}
    inh = d.get('inherits', '')
    for parent in [p.strip() for p in inh.split(';') if p.strip()]:
        res.update(resolve(kind, parent, depth+1))
    res.update({k: v for k, v in d.items() if k != 'inherits'})
    return res
cfg = {}
for kind in ('printer', 'print', 'filament'):
    r = resolve(kind, sel[kind])
    for k in ('compatible_printers', 'compatible_printers_condition', 'compatible_prints', 'compatible_prints_condition', 'renamed_from', 'alias', 'inherits'):
        r.pop(k, None)
    cfg.update(r)
cfg['printer_settings_id'] = sel['printer']; cfg['print_settings_id'] = sel['print']; cfg['filament_settings_id'] = sel['filament']
with io.open(out, 'w', encoding='utf-8') as f:
    for k in sorted(cfg): f.write(f'{k} = {cfg[k]}\n')
print(len(cfg), 'keys;', 'model', cfg.get('printer_model'), 'bed', cfg.get('bed_shape'), 'fil', cfg.get('filament_type'), 'maxvol', cfg.get('filament_max_volumetric_speed'))
