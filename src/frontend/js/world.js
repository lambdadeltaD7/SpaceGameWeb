const base_url = "http://localhost:8004" 


const status_bar = document.getElementById('status_bar');
const world_info_txt = document.getElementById('world_info_txt');
const space = document.getElementById('space');
const game_grid = document.getElementById('game_grid');

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

async function render_world(world_info, planets) {
    

    const w = world_info.w;
    const h = world_info.h;
    
    var grid = Array.from({length:h}, () => new Array(w).fill(0));

    for(const p of planets){
        grid[p.y][p.x] = 1;
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
