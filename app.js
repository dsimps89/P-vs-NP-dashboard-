let catalog = null;

async function loadCatalog(){

    const response = await fetch("catalog.json");

    catalog = await response.json();

    document.getElementById("stats").innerHTML = `
        <h3>Statistics</h3>

        <p>
            Total Problems:
            ${catalog.totalProblems}
        </p>

        <p>
            Database:
            ${catalog.categories.database_problems}
        </p>

        <p>
            Flow:
            ${catalog.categories.flow_problems}
        </p>

        <p>
            Graph:
            ${catalog.categories.graph_theory}
        </p>

        <p>
            Network:
            ${catalog.categories.network_design}
        </p>
    `;

    render(catalog.problems);
}

function render(problems){

    let html = "";

    problems.forEach(problem => {

        html += `
            <div class="card"
                 onclick="showProblem('${problem.id}')">

                <div class="title">
                    ${problem.title}
                </div>

                <div>
                    ${problem.category}
                </div>

            </div>
        `;
    });

    document.getElementById("results").innerHTML = html;
}

function showProblem(id){

    const p =
        catalog.problems.find(x => x.id === id);

    if(!p) return;

    document.getElementById("detail").innerHTML = `

        <h2>${p.title}</h2>

        <p>
            <span class="badge">
                ${p.category}
            </span>
        </p>

        <h3>Basic Information</h3>

        <p><b>ID:</b> ${p.id}</p>

        <p><b>Name:</b> ${p.name}</p>

        <p><b>Category:</b> ${p.category}</p>

        <p><b>Complexity:</b>
        ${p.complexity || "Unknown"}
        </p>

        <p><b>Family:</b>
        ${p.family || "Unknown"}
        </p>

        <h3>Keywords</h3>

        <pre>
${JSON.stringify(p.keywords || [], null, 2)}
        </pre>

        <h3>Related Problems</h3>

        <pre>
${JSON.stringify(p.related || [], null, 2)}
        </pre>
    `;
}

function applyFilters(){

    if(!catalog) return;

    const search =
        document
        .getElementById("search")
        .value
        .toLowerCase();

    const category =
        document
        .getElementById("category")
        .value;

    const filtered =
        catalog.problems.filter(problem => {

            const matchesSearch =
                problem.title
                .toLowerCase()
                .includes(search)

                ||

                problem.name
                .toLowerCase()
                .includes(search);

            const matchesCategory =
                category === "all"

                ||

                problem.category === category;

            return (
                matchesSearch &&
                matchesCategory
            );
        });

    render(filtered);
}

document
.getElementById("search")
.addEventListener(
    "input",
    applyFilters
);

document
.getElementById("category")
.addEventListener(
    "change",
    applyFilters
);

loadCatalog();
