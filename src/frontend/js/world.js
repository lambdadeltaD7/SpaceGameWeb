const base_url = "http://localhost:8004" 


const status_bar = document.getElementById('status_bar');
const world_info_txt = document.getElementById('world_info_txt');

const space = document.getElementById('space');
const game_grid = document.getElementById('game_grid');

// const planet_info_card = document.getElementById('planet_info_card');


const shield_dialog = document.getElementById('shield_dialog');
const shield_dialog_txt = document.getElementById('shield_dialog_txt');
const shield_dialog_btn_ok = document.getElementById('shield_dialog_btn_ok');
const shield_dialog_btn_cancel = document.getElementById('shield_dialog_btn_cancel');

var world_id = null;
var planet_info_card_id = null;

{/* <div id="planet_info_card" style="position: absolute; top: 10%;
     left: 30%; border: solid black 5px;
     background-color: cadetblue; color: black; display: none;"></div>

<div id="shield_dialog" style="position: absolute; top: 10%;
    left: 30%; border: solid black 5px; flex-direction: column;
    background-color: cadetblue; color: black; display: none;">
    <p id="shield_dialog_txt"></p>
    <button id="shield_dialog_btn_ok">change shield status</button>
    <button id="shield_dialog_btn_cancel">cancel</button>
</div> */}

var old_status_text = null;


function showErr(txt){
    Swal.fire({
            icon: 'error',
            title: 'Input error',
            text: txt,
            });
}

function showToast(txt){
    Swal.fire({
        toast: true,
        position: 'top-end',
        icon: 'success',
        title: txt,
        showConfirmButton: false,
        timer: 2000,
        timerProgressBar: true
        });
}


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


    old_status_text = world_info_txt.textContent;

    const planets = await get_world_planets();

    render_world(world_info, planets);

}


function on_mouse_enter_planet(planet_info){
    console.log(planet_info);
    world_info_txt.textContent = `
        planet_id = ${planet_info.planet_id},
        res1 = ${planet_info.res1},
        res2 = ${planet_info.res2},
        shield_on = ${planet_info.shield_on},
    `;

}


function on_mouse_leave_planet(){
    world_info_txt.textContent = old_status_text;
}


function init_planet_cell(curr_cell, planet_info){
    curr_cell.addEventListener('mouseenter', () => {on_mouse_enter_planet(planet_info)});
    curr_cell.addEventListener('mouseleave', on_mouse_leave_planet);
    curr_cell.addEventListener('click', () => {on_mouse_click_planet(planet_info)});
}


async function render_world(world_info, planets) {
    

    const w = world_info.w;
    const h = world_info.h;
    
    var grid = Array.from({length:h}, () => new Array(w).fill(0));

    var p_dict = {};

    for(var p of planets){
        console.log(p);
        grid[p.y][p.x] = 1;
        if(p.shield_on){
            grid[p.y][p.x] = 2;
        }
        p_dict[`${p.y}_${p.x}`] = p;
    }

    console.log(p_dict);

    const cell_w = 100 / w;

    console.log(grid);

    game_grid.innerHTML = '';

    for(var i=0; i<h; ++i){
        const curr_row = document.createElement('div');
        curr_row.style = "display: flex; flex-direction: row";
        for(var j=0; j<w; ++j){
            var curr_cell = document.createElement('div');
            if(grid[i][j]==1){
                curr_cell.style.backgroundColor = "black";
                init_planet_cell(curr_cell, p_dict[`${i}_${j}`]);
            }
            else if (grid[i][j]==2){
                curr_cell.style.backgroundColor = "green";
                init_planet_cell(curr_cell, p_dict[`${i}_${j}`]);
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


async function on_mouse_click_planet(planet_info){

    const shield_dialog = document.createElement('div');
    shield_dialog.id = `shield_dialog_id_${planet_info.planet_id}`;
    
    shield_dialog.style =
        "position: absolute; top: 10%;" +
        "left: 30%; border: solid black 5px; flex-direction: column;" +
        "background-color: cadetblue; color: black;";

    const shield_dialog_txt = document.createElement('p');
    const shield_dialog_btn_ok = document.createElement('button');
    const shield_dialog_btn_cancel = document.createElement('button');

    shield_dialog_btn_ok.textContent = 'change shield status';
    shield_dialog_btn_cancel.textContent = 'cancel';

    shield_dialog_txt.textContent = `shield menu for planet_id=${planet_info.planet_id}\n`;
    if(planet_info.shield_on){
        shield_dialog_txt.textContent += 'right now shield is active\n';
    }
    else{
        shield_dialog_txt.textContent += 'right now shield is NOT active\n';
    }
    shield_dialog_txt.textContent += 'when active shield consumes N res1 per sec\n';
    shield_dialog_txt.textContent += 'change shield status?\n';
    shield_dialog.append(shield_dialog_txt);
    shield_dialog.append(shield_dialog_btn_ok);
    shield_dialog.append(shield_dialog_btn_cancel);

    shield_dialog_btn_ok.addEventListener('click', async () => {
        
        const result = await fetch(
        base_url + `/api/v1/planets/${planet_info.planet_id}?shield_on=${!planet_info.shield_on}`,
            {
                method: 'PATCH',
            }
        );

        if(result.ok){
            document.getElementById(shield_dialog.id).style.display="none";
            document.getElementById(shield_dialog.id).remove();
            await init();
        }
        else{
            const data = await result.json();
            showErr(data.detail);
            document.getElementById(shield_dialog.id).remove();
        }
        
    });


    shield_dialog_btn_cancel.addEventListener('click', () => {
        shield_dialog.style.display = "none";
        document.getElementById(shield_dialog.id).remove();
    });

    document.getElementById('doc_body').append(shield_dialog);
}





queueMicrotask(async () => {await init();});
