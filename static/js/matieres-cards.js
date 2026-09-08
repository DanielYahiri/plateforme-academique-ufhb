// Rendu des cartes matières — chemin image déduit localement, aucune dépendance Supabase

function cheminImageMatiere(m) {
  const niveau = (m.niveau_scolaire || "").trim();
  const sem = m.sem_mat != null ? `S${m.sem_mat}` : "";
  const code = (m.code_mat || "").trim();
  return `/static/img/matieres/${niveau}_${sem}_${code}.jpg`;
}

function afficherMatieres(data) {
  const grid = document.getElementById("matieresGrid");
  const empty = document.getElementById("matieresEmpty");
  if (!Array.isArray(data) || data.length === 0) {
    grid.innerHTML = "";
    empty.classList.remove("hidden");
    return;
  }
  empty.classList.add("hidden");
  grid.innerHTML = data.map(m => {
    const img = cheminImageMatiere(m);
    return `
    <a href="/matieres/${encodeURIComponent(m.code_mat)}" class="matiere-card">
      <div class="matiere-image">
        <img src="${img}" alt="${m.nom_mat}"
             onerror="this.onerror=null;this.outerHTML='<i class=\\'fas fa-book\\'></i>';">
      </div>
      <div class="matiere-body">
        <p class="matiere-nom">${m.nom_mat}</p>
        <p class="matiere-meta">${m.niveau_scolaire || ""}${m.sem_mat ? " · S" + m.sem_mat : ""}</p>
      </div>
    </a>`;
  }).join("");
}

async function chargerMatieres() {
  document.getElementById("matieresLoading").classList.remove("hidden");
  document.getElementById("matieresEmpty").classList.add("hidden");
  try {
    const r = await fetch("/api/matieres");
    const data = await r.json();
    afficherMatieres(data);
  } catch (e) {
    console.error("Erreur chargement matières :", e);
  } finally {
    document.getElementById("matieresLoading").classList.add("hidden");
  }
}

async function appliquerFiltreMatieres() {
  document.getElementById("matieresLoading").classList.remove("hidden");
  const niveau = document.getElementById("filtreNiveau").value || null;
  const semestreVal = document.getElementById("filtreSemestre").value;
  const semestre = semestreVal ? parseInt(semestreVal, 10) : null;
  try {
    const r = await fetch("/api/matieres/filter", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ p_niveau_scolaire: niveau, p_sem_mat: semestre }),
    });
    const data = await r.json();
    afficherMatieres(data);
  } catch (e) {
    console.error("Erreur filtrage matières :", e);
  } finally {
    document.getElementById("matieresLoading").classList.add("hidden");
  }
}

function reinitialiserFiltreMatieres() {
  document.getElementById("filtreNiveau").value = "";
  document.getElementById("filtreSemestre").value = "";
  chargerMatieres();
}

chargerMatieres();