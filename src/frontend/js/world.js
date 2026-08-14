const base_url = "http://localhost:8004" 


const status_bar = document.getElementById('status_bar');
const world_info_txt = document.getElementById('world_info_txt');
const space = document.getElementById('space');
const game_grid = document.getElementById('game_grid');
const planet_info_card = document.getElementById('planet_info_card');

var world_id = null;

async function init() {
    world_id = await cookieStore.get('world_id');
    world_id = world_id.value;
    console.log(`world_id is ${world_id}`);

    const world_info = await get_world_info();

    world_info_txt.textContent = `
    owner_id: ${world_info.user_id}
    world_id: ${world_info.world_id} 
    seed: ${world_info.seed}
    size: (w,h) = (${world_info.w},${world_info.h})
    `;

    const planets = await get_world_planets();

    render_world(world_info, planets);

}

function on_mouse_enter_planet(planet_info){
    planet_info_card.textContent = `
        planet_id = ${planet_info.planet_id},
        res1 = ${planet_info.res1},
        res2 = ${planet_info.res2},
        shield_on = ${planet_info.shield_on},
    `;
    planet_info_card.style.display = 'block'
}

function on_mouse_leave_planet(){
    planet_info_card.style.display = 'none'
    planet_info_card.textContent = '';
}


function attach_info_display(curr_cell, planet_info){
    curr_cell.addEventListener('mouseenter', () => {on_mouse_enter_planet(planet_info)});
    curr_cell.addEventListener('mouseleave', on_mouse_leave_planet);
}


async function render_world(world_info, planets) {
    

    const w = world_info.w;
    const h = world_info.h;
    
    var grid = Array.from({length:h}, () => new Array(w).fill(0));

    var p_dict = {};

    for(const p of planets){
        grid[p.y][p.x] = 1;
        if(p.shield_on){
            grid[p.y][p.x] = 2;
        }
        p_dict[(p.y, p.x)] = p;
    }

    const cell_w = 100 / w;

    console.log(grid);

    game_grid.innerHTML = '';

    for(var i=0; i<h; ++i){
        const curr_row = document.createElement('div');
        curr_row.style = "display: flex; flex-direction: row";
        for(var j=0; j<w; ++j){
            const curr_cell = document.createElement('div');
            if(grid[i][j]==1){
                curr_cell.style.backgroundColor = "black";
                attach_info_display(curr_cell, p_dict[(i, j)]);
            }
            else if (grid[i][j]==2){
                curr_cell.style.backgroundColor = "green";
                attach_info_display(curr_cell, p_dict[(i, j)]);
            }
            else{
                curr_cell.style.backgroundColor = "blue";
            }
            
            curr_cell.style.width = `30px`;
            curr_cell.style.height = "30px";
            curr_row.append(curr_cell);
        }
        game_grid.append(curr_row);
    }
}


async function get_world_info() {
    const result = await fetch(base_url + `/api/v1/worlds/${world_id}`);
    const data = await result.json();
    return data;
}

async function get_world_planets() {
    const result = await fetch(base_url + `/api/v1/planets/?world_id=${world_id}`);
    const data = await result.json();
    return data;
}


queueMicrotask(async () => {await init();});
