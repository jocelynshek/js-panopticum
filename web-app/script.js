const width = window.innerWidth;
const height = window.innerHeight;

let allNetworks;
let hasShifted = false;


Promise.all([
  d3.json("../joc-data/topics.json"),
  d3.json("../joc-data/networks.json")
]).then(([topics, networks]) => {
  allNetworks = networks;
  drawBubbles(topics);
});

function drawBubbles(topics) {
  const svg = d3.select("#chart").append("svg")
    .attr("viewBox", [0, 0, width, height]);

  const leftGroup = svg.append("g").attr("class", "packed-bubbles");
  const rightGroup = svg.append("g").attr("class", "bar-chart");

  const radiusScale = d3.scaleSqrt()
    .domain(d3.extent(topics, d => d.count))
    .range([width * 0.02, width * 0.08]);

  const customPalette = [
      "#ff805b", "#ffbc35", "#ffeac0", //"#457b9d",
      "#8ecae6", "#219ebc"
    ];
    
  const color = d3.scaleOrdinal()
    .domain([...new Set(topics.map(d => d.group))]) // ensure groups are mapped
    .range(customPalette);
    

  topics.forEach(d => {
    d.x = width / 2 + (Math.random() - 0.5) * 200;
    d.y = height / 2 + (Math.random() - 0.5) * 200;
  });

  
  topics.sort((a, b) => d3.descending(a.count, b.count));

  const node = leftGroup.selectAll("circle")
    .data(topics)
    .enter().append("circle")
    .attr("r", d => radiusScale(d.count))
    .attr("fill", d => color(d.group))
    .attr("stroke", "#333")
    .attr("stroke-width", 0.5)
    .style("cursor", "pointer")
    .on("click", (event, d) => transitionToNetwork(d.id))
    .on("mouseover", (event, d) => {
      if (!hasShifted) {
        leftGroup.transition().duration(300)
          .attr("transform", `translate(-${width * 0.2}, 0)`);
        hasShifted = true;
      }
      showTopWords(d, rightGroup);
    })
    .on("mouseout", () => {
      rightGroup.selectAll("*").remove();  // Don't reset transform
    });
    

  node.append("title")
    .text(d => `#${d.id} ${d.label}`);

  const labels = leftGroup.selectAll("text")
    .data(topics)
    .enter()
    .append("text")
    .attr("font-size", "10px")
    .attr("text-anchor", "middle")
    .attr("fill", "#333")
    .text(d => d.manualLabel);

  d3.forceSimulation(topics)
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collide", d3.forceCollide(d => radiusScale(d.count) + 2))
    .force("x", d3.forceX(d => width / 2).strength(d => 0.02 + 0.08 * (d.count / d3.max(topics, t => t.count))))
    .force("y", d3.forceY(d => height / 2).strength(d => 0.02 + 0.08 * (d.count / d3.max(topics, t => t.count))))
    .on("tick", () => {
      node.attr("cx", d => d.x).attr("cy", d => d.y);
      labels.attr("x", d => d.x).attr("y", d => d.y + 4);
    });

}

function showTopWords(topic, rightGroup) {
  const data = (topic.topWords || []).slice().sort((a, b) => d3.descending(a.value, b.value));


  const x = d3.scaleLinear()
    .domain([0, d3.max(data, d => d.value)])
    .range([0, width * 0.25]);

  const y = d3.scaleBand()
    .domain(data.map(d => d.word))
    .range([height * 0.25, height * 0.75])
    .padding(0.1);

  rightGroup.append("text")
  .attr("x", width * 0.65)
  .attr("y", height * 0.2)
  .attr("fill", "#111")
  .attr("font-size", "12px")
  .attr("font-weight", "bold")
  .text(`${topic.manualLabel || topic.label}: ${topic.count} articles in group`);

  // Chart subtitle
rightGroup.append("text")
.attr("x", width * 0.65)
.attr("y", height * 0.23)
.attr("fill", "#333")
.attr("font-size", "11px")
.text("Percent of articles in category each term appears in:");


  // Draw bars
  rightGroup.selectAll("rect")
    .data(data)
    .join("rect")
    .attr("x", width * 0.65)
    .attr("y", d => y(d.word))
    .attr("width", d => x(d.value))
    .attr("height", y.bandwidth())
    .attr("fill", "#555");

  // Word labels
  rightGroup.selectAll("text.word-label")
    .data(data)
    .join("text")
    .attr("class", "word-label")
    .attr("x", width * 0.65 - 10)
    .attr("y", d => y(d.word) + y.bandwidth() / 2)
    .attr("dy", "0.35em")
    .attr("text-anchor", "end")
    .attr("fill", "#333")
    .attr("font-size", "10px")
    .text(d => d.word);

    
  // Value markers
  rightGroup.selectAll("text.value-label")
  
    .data(data)
    .join("text")
    .attr("class", "value-label")
    .attr("x", d => width * 0.65 + x(d.value) + 5)
    .attr("y", d => y(d.word) + y.bandwidth() / 2)
    .attr("dy", "0.35em")
    .attr("text-anchor", "start")
    .attr("fill", "#555")
    .attr("font-size", "9px")
    .text(d => `${d.value}%`);
    
}


function transitionToNetwork(topicId) {
  d3.select("#chart")
    .transition().duration(400)
    .style("opacity", 0)
    .on("end", () => d3.select("#chart").style("pointer-events", "none"));

  d3.select("#network")
    .style("pointer-events", "all")
    .transition().duration(400)
    .style("opacity", 1);

  showNetwork(topicId);
}

function showNetwork(topicId) {
  d3.select("#network").html("");

  const graph = allNetworks.find(n => n.topic === topicId);
  if (!graph) return;

  const svg = d3.select("#network").append("svg")
    .attr("viewBox", [0, 0, width, height])
    .attr("preserveAspectRatio", "xMidYMid meet");

  const rScale = d3.scaleSqrt()
    .domain(d3.extent(graph.nodes.map(d => d.size)))
    .range([4, 20]);

  
  const customColors = [
      "#ffbc35", "#4690ff", "#ff805b", "#ffeac0", "#ffbc35",
    ];
    
  const groupIds = [...new Set(graph.nodes.map(d => d.group))];

  const color = d3.scaleOrdinal()
    .domain(groupIds)
    .range(customColors);
    

  const link = svg.append("g")
    .selectAll("line")
    .data(graph.links)
    .enter().append("line")
    .attr("stroke", "#d4d2d2")
    .attr("stroke-width", d => Math.sqrt(d.value));

  const node = svg.append("g")
    .selectAll("circle")
    .data(graph.nodes)
    .enter().append("circle")
    .attr("r", d => rScale(d.size))
    .attr("fill", d => color(d.group))
    .attr("stroke", "#333")
    .attr("stroke-width", 0.5)
    .call(d3.drag()
      .on("start", event => {
        if (!event.active) sim.alphaTarget(0.3).restart();
        event.subject.fx = event.subject.x;
        event.subject.fy = event.subject.y;
      })
      .on("drag", event => {
        event.subject.fx = event.x;
        event.subject.fy = event.y;
      })
      .on("end", event => {
        if (!event.active) sim.alphaTarget(0);
        event.subject.fx = null;
        event.subject.fy = null;
      }));

  const label = svg.append("g")
    .selectAll("text")
    .data(graph.nodes)
    .enter().append("text")
    .text(d => d.id)
    .attr("font-size", "8px");

    const centerX = width / 2;
    const centerY = height / 2;

    const MARGIN_X = width * 0.125;  // 12.5% on each side = 25% total
    const MARGIN_Y = height * 0.125;

    const centerBoxX = d3.forceX(d => {
      if (d.x < MARGIN_X) return MARGIN_X;
      if (d.x > width - MARGIN_X) return width - MARGIN_X;
      return d.x;
    }).strength(0.1);

    const centerBoxY = d3.forceY(d => {
      if (d.y < MARGIN_Y) return MARGIN_Y;
      if (d.y > height - MARGIN_Y) return height - MARGIN_Y;
      return d.y;
    }).strength(0.1);


    const connectedIds = new Set(graph.links.flatMap(d => [d.source, d.target]));
    graph.nodes.forEach(d => {
      d.unconnected = !connectedIds.has(d.id);
    });
    
    const sim = d3.forceSimulation(graph.nodes)
    .force("link", d3.forceLink(graph.links).id(d => d.id).distance(80))
    .force("charge", d3.forceManyBody().strength(-150))
    .force("center", d3.forceCenter(centerX, centerY))  // optional — still nice for balance
    .force("bounded-x", centerBoxX)
    .force("bounded-y", centerBoxY)
    .on("tick", () => {
      link
        .attr("x1", d => d.source.x).attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
  
      node
        .attr("cx", d => d.x)
        .attr("cy", d => d.y);
  
      label
        .attr("x", d => d.x)
        .attr("y", d => d.y);
    });
  
    

    
  d3.select("#network").append("button")
    .text("← Back")
    .on("click", () => {
      d3.select("#network")
        .transition().duration(400)
        .style("opacity", 0)
        .on("end", () => d3.select("#network").style("pointer-events", "none"));

      d3.select("#chart")
        .style("pointer-events", "all")
        .transition().duration(400)
        .style("opacity", 1);
    });
}