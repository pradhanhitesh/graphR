// Variables
const toogleThemeButton = document.getElementById("toogle-theme-button");
const searchButton = document.querySelector("#toogle-search-button");
const width = window.innerWidth;
const height = window.innerHeight;

// SwiperJS Function
var swiper = new Swiper(".mySwiper", {
    slidesPerView: 1,
    spaceBetween: 30,
    grabCursor: true,
    loop: false,
    pagination: {
        el: ".swiper-pagination",
        clickable: true,
    },
    navigation: {
        nextEl: ".swiper-button-next",
        prevEl: ".swiper-button-prev",
    },
});

// Toggle theme button functionality [Light/Dark Mode]
toogleThemeButton.addEventListener("click", () => {
    const isLightMode = document.body.classList.toggle("light_mode"); // Toggle light mode class
    localStorage.setItem("themeColor", isLightMode ? "light_mode" : "dark_mode");  // Store the current theme in localStorage
    toogleThemeButton.innerText = isLightMode ? "dark_mode" : "light_mode"; // Update button text
});

// Function to load theme from localStorage
const loadLocalStorageData = () => {
    const isLightMode = (localStorage.getItem("themeColor") === "light_mode");

    // Toggle light mode class based on saved preference
    document.body.classList.toggle("light_mode", isLightMode);
    toogleThemeButton.innerText = isLightMode ? "dark_mode" : "light_mode";
}

// Load saved chats when the script runs
loadLocalStorageData();

// Add click event listener to the search button
searchButton.addEventListener('click', () => {
    window.location.href = '/';
});

// D3.JS Functions
const svg = d3.select('.graph-container svg')
    .attr('viewBox', `0 0 900 600`) // Visible area dimensions of the SVG content
    .attr('preserveAspectRatio', 'xMidYMid meet'); // Center the content

// Create a container for zoom/pan
const container = svg.append("g");

// Load the data
const rawData = JSON.parse(localStorage.getItem('rawData'));
const communityData = JSON.parse(localStorage.getItem('communityData'));
const graphData = JSON.parse(localStorage.getItem('graphData'));
const profileID = localStorage.getItem('profileID');
const data = rawData.filter(d => d['Composite'] > 0);

// Prepare nodes and links
const nodes = [];
const links = [];

data.forEach((d) => {
    const paper1 = d['Paper 1'];
    const paper2 = d['Paper 2'];
    const overlap = d['Composite'];

    // Add paper1 node if it doesn't already exist
    if (!nodes.some(n => n.id === paper1)) {
        nodes.push({ id: paper1, index: nodes.length });
    }

    // Add paper2 node if it doesn't already exist
    if (!nodes.some(n => n.id === paper2)) {
        nodes.push({ id: paper2, index: nodes.length });
    }

    // Create a link between paper1 and paper2
    links.push({
        source: paper1,
        target: paper2,
        value: overlap * 6 // Scale overlap value
    });
});

// Create a dictionary for quick lookup where key is the paper name and value is the community
const communityDict = communityData.reduce((acc, entry, index) => {
    acc[entry['Paper Name']] = entry['Community'];  // entry[1] is the paper name, entry[0] is the community
    return acc;
}, {});


// Initialize arrays to store node indices for each community
let community1idx = [];
let community2idx = [];
let community3idx = [];

// Loop through each node and extract the node index and corresponding community
nodes.forEach(node => {
    const nodeTitle = node.id;
    const community = communityDict[nodeTitle] || 'No community assigned';  // Handle missing community info

    // Add the node index to the corresponding community array based on the community value
    if (community === '1') {
        community1idx.push(node.index);
    } else if (community === '2') {
        community2idx.push(node.index);
    } else if (community === '3') {
        community3idx.push(node.index);
    }
});

// D3 force simulation
const simulation = d3.forceSimulation(nodes)
    .force("link", d3.forceLink(links)
        .id(d => d.id)
        .distance(d => 300 / (d.value / 5)) // Distance inversely proportional to overlap
    )
    .force("charge", d3.forceManyBody().strength(-400))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collide", d3.forceCollide(30))
    

// Tooltip setup
const tooltip = d3.select("body").append("div")
    .attr("class", "tooltip");

// Draw links
const link = container.append("g")
    .selectAll(".link")
    .data(links)
    .enter().append("line")
    .attr("class", "link")
    .attr("stroke-width", d => d.value);

// Draw nodes
const node = container.append("g")
    .selectAll(".node")
    .data(nodes)
    .enter().append("circle")
    .attr("class", "node")
    .attr("r", 15)
    .attr("fill", "grey")
    .on("mouseover", (event, d) => {
        tooltip
            .style("opacity", 1)
            .html(d.id)
            .style("left", (event.pageX + 10) + "px")
            .style("top", (event.pageY - 20) + "px");
    })
    .on("mousemove", (event) => {
        tooltip
            .style("left", (event.pageX + 10) + "px")
            .style("top", (event.pageY - 20) + "px");
    })
    .on("mouseout", () => {
        tooltip.style("opacity", 0);
    })
    .on("click", (event, d) => {
        highlightLinks(d); // Highlight the links connected to the clicked node
        updatePaperDetails(d.id); // Call updatePaperDetails with the node's ID
    })
    .call(d3.drag()
        .on("start", dragstart)
        .on("drag", dragged)
        .on("end", dragend));


// Initial zoom value and position
const initialScale = 0.25; // Adjust as needed
const initialTranslateX = width / 5; // Center the graph horizontally
const initialTranslateY = height / 3; // Center the graph vertically

// Zoom and pan behavior with initial zoom
const zoomBehavior = d3.zoom()
    .scaleExtent([0.1, 4]) // Min and max zoom levels
    .on("start", () => {
        svg.style("cursor", "grab"); // Change cursor to grab on zoom start
    })
    .on("zoom", (event) => {
        container.attr("transform", event.transform);
        svg.style("cursor", "grabbing"); // Change cursor to grabbing while moving
    })
    .on("end", () => {
        svg.style("cursor", "default"); // Reset cursor to default after zoom
    });

// Apply the zoom behavior to the SVG
svg.call(zoomBehavior);

// Set the initial zoom transform
svg.call(
    zoomBehavior.transform,
    d3.zoomIdentity
        .translate(initialTranslateX, initialTranslateY) // Initial translation
        .scale(initialScale) // Initial scale
);

// Update positions during simulation
simulation.on("tick", () => {
    link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);

    node
        .attr("cx", d => d.x)
        .attr("cy", d => d.y);
});

// Define cluster centers for each community
const clusterCenters = {
    '1': { x: width / 4, y: height / 2 },
    '2': { x: width / 2, y: height / 2 },
    '3': { x: (3 * width) / 4, y: height / 2 },
};
const fallbackCenter = { x: width / 2, y: height / 2 };

// Assign initial positions to nodes based on community
nodes.forEach(node => {
    const community = communityDict[node.id] || null;
    if (community && clusterCenters[community]) {
        node.x = clusterCenters[community].x + Math.random() * 50 - 25;
        node.y = clusterCenters[community].y + Math.random() * 50 - 25;
    } else {
        node.x = fallbackCenter.x + Math.random() * 50 - 25;
        node.y = fallbackCenter.y + Math.random() * 50 - 25;
    }
});

// Add forces to maintain clusters during simulation
simulation
    .force("clusterX", d3.forceX(d => clusterCenters[communityDict[d.id]]?.x || fallbackCenter.x).strength(0.1))
    .force("clusterY", d3.forceY(d => clusterCenters[communityDict[d.id]]?.y || fallbackCenter.y).strength(0.1))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collide", d3.forceCollide(15));

// Node drag events
function dragstart(event) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    event.subject.fx = event.subject.x;
    event.subject.fy = event.subject.y;
}

function dragged(event) {
    event.subject.fx = event.x;
    event.subject.fy = event.y;
}

function dragend(event) {
    if (!event.active) simulation.alphaTarget(0);
    event.subject.fx = null;
    event.subject.fy = null;
}

// Reset highlights and node sizes when clicking outside nodes
svg.on("click", (event) => {
    const clickedElement = event.target;

    if (!clickedElement.classList.contains("node")) {
        link.style("opacity", 0.1); // Default opacity for all links
        node.attr("r", 15); // Reset node sizes
        link.style("stroke", "#999"); // Reset link colors
    }
});

function getNodeColor(d, activeSlider, clickedCommunity = null) {
    const nodeCommunity = communityDict[d.id];

    // If a node is clicked, highlight its community
    if (clickedCommunity !== null) {
        return nodeCommunity === clickedCommunity ? colorScale(nodeCommunity) : "grey";
    }

    // Otherwise, use the active slider to determine colors
    if (nodeCommunity === activeSlider) {
        return colorScale(nodeCommunity);
    }

    return "grey"; // Default color for nodes not in the active community
}


// Assuming you have a variable that tracks the active slider number
let activeSlider = 1;

// Listen for slider changes to update the activeSlider variable
swiper.on('slideChange', function () {
    const newActiveSlider = swiper.activeIndex + 1; // Slider index is zero-based, so add 1
    console.log(newActiveSlider);
    if (activeSlider !== newActiveSlider) {
        activeSlider = newActiveSlider;
        highlightNodesBasedOnSlider(activeSlider);
    }
});

// Unified color scale for both sliders and communities
const colorScale = d3.scaleOrdinal()
    .domain([1, 2, 3]) // Community numbers
    .range(["blue", "blue", "blue"]); // Colors for communities

    function highlightNodesBasedOnSlider(sliderNumber) {
        if (!node || !link) {
            console.warn("Nodes or links are not initialized.");
            return;
        }
    
        node.attr("fill", (d, index) => {
            if (community1idx.includes(index)) {
                return sliderNumber === 1 ? colorScale(1) : "grey";
            } else if (community2idx.includes(index)) {
                return sliderNumber === 2 ? colorScale(2) : "grey";
            } else if (community3idx.includes(index)) {
                return sliderNumber === 3 ? colorScale(3) : "grey";
            } else {
                return "grey";
            }
        });
    
        node.attr("r", (d, index) => {
            if (community1idx.includes(index) && sliderNumber === 1) {
                return 50;
            } else if (community2idx.includes(index) && sliderNumber === 2) {
                return 50;
            } else if (community3idx.includes(index) && sliderNumber === 3) {
                return 50;
            } else {
                return 15;
            }
        });
    
        // Adjust link opacity based on the slider
        link.style("opacity", (d) => {
            const sourceCommunity = communityDict[d.source.id];
            const targetCommunity = communityDict[d.target.id];
    
            // Increase opacity for links within the active community
            return sourceCommunity === sliderNumber || targetCommunity === sliderNumber ? 1 : 0.2;
        });
    }
    
// Initial highlight
if (node) {
    highlightNodesBasedOnSlider(activeSlider);
}

// Function to update the paper details dynamically
function updatePaperDetails(paperName) {
    const paper = communityData.find(p => p["Paper Name"] === paperName);

    if (paper) {
        document.getElementById('paper-title').innerHTML = `<h3>${paper["Paper Name"]}</h3>`;
        document.getElementById('paper-authors').innerHTML = paper["Paper Authors"];
        
        const description = paper["Paper Description"];
        const descriptionContainer = document.getElementById('paper-sections');
        descriptionContainer.innerHTML = "";

        if (description && Object.keys(description).length > 0) {
            Object.entries(description).forEach(([section, text]) => {
                const sectionElement = document.createElement('div');
                sectionElement.classList.add('paper-section');
                sectionElement.innerHTML = `
                    <h4>${section}</h4>
                    <p>${text}</p>
                `;
                descriptionContainer.appendChild(sectionElement);
            });
            const graphPapersDiv = document.querySelector('.graph-papers');
            graphPapersDiv.scrollTo({
                top: 0,
                behavior: 'smooth' // Enables smooth scrolling
            });
        } else {
            descriptionContainer.innerHTML = "<p>No description available.</p>";
        }
    } else {
        console.warn(`Paper details not found for: ${paperName}`);
        document.getElementById('paper-title').innerHTML = `<h3>${paperName}</h3>`;
        document.getElementById('paper-authors').innerHTML = `Authors not available`;
        const descriptionContainer = document.getElementById('paper-sections');
        descriptionContainer.innerHTML = "";
        descriptionContainer.innerHTML += `<p>Description not available</p>`;
    }
}


// Define mapping from community to slide index
const communityToSlideIndex = {
    1: 0, // Community 1 -> Slide 1
    2: 1, // Community 2 -> Slide 2
    3: 2, // Community 3 -> Slide 3
};

// Highlight nodes of the same community
function highlightCommunity(clickedNode) {
    const clickedCommunity = communityDict[clickedNode.id];
    console.log(clickedCommunity);
    
    if (!clickedCommunity) {
        console.warn("No community assigned to the clicked node.");
        return;
    }

    node.attr("fill", (d) => {
        const nodeCommunity = communityDict[d.id];
        return nodeCommunity === clickedCommunity
            ? colorScale(nodeCommunity) // Highlighted color
            : "grey"; // Dimmed color for other nodes
    });

    node.attr("r", (d) => {
        const nodeCommunity = communityDict[d.id];
        return nodeCommunity === clickedCommunity ? 50 : 15; // Adjust radius
    });

    link.style("stroke", "#999"); // Reset link colors
    link.style("opacity", 0.2)

    if (communityToSlideIndex[clickedCommunity] !== undefined) {
        swiper.slideTo(communityToSlideIndex[clickedCommunity]);
    }
}

// Node click handler
node.on("click", (event, d) => {
    console.log(d);
    highlightCommunity(d);
    updatePaperDetails(d.id);
});

const slides = [
    { nameId: 'comm-1-name', descId: 'comm-1-desc', dataKey: 'community_1' },
    { nameId: 'comm-2-name', descId: 'comm-2-desc', dataKey: 'community_2' },
    { nameId: 'comm-3-name', descId: 'comm-3-desc', dataKey: 'community_3' },
];

slides.forEach(({ nameId, descId, dataKey }) => {
    const nameElement = document.getElementById(nameId);
    const descElement = document.getElementById(descId);

    if (nameElement && descElement && graphData[profileID][dataKey]) {
        const { short_name, summary } = graphData[profileID][dataKey];
        nameElement.innerText = short_name;
        descElement.innerText = summary;
    }
});



