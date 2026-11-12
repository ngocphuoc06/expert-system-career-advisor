(function () {
	"use strict";

	const form = document.getElementById("advisor-form");
	const count = document.getElementById("selected-count");
	const error = document.getElementById("form-error");
	const knowledgeStatus = document.getElementById("knowledge-status");
	const resultSection = document.getElementById("results");
	const explanationList = document.getElementById("explanation-list");
	const traceList = document.getElementById("trace-list");
	const recommendationList = document.getElementById("recommendation-list");
	const derivedFacts = document.getElementById("derived-facts");
	const intermediateResults = document.getElementById("intermediate-results");
	const noResults = document.getElementById("no-results");
	const scoreNames = {
		Diem_Toan: "Toán",
		Diem_Ly: "Vật lý",
		Diem_Hoa: "Hóa học",
		Diem_Sinh: "Sinh học",
		Diem_Tin: "Tin học",
		Diem_Van: "Ngữ văn",
		Diem_Su: "Lịch sử",
		Diem_Dia: "Địa lý",
		Diem_Anh: "Tiếng Anh",
		Diem_Ve: "Năng khiếu vẽ"
	};
	const interestNames = {
		May_Moc: "Máy móc",
		Lap_Trinh: "Lập trình",
		Nghien_Cuu: "Nghiên cứu",
		Sang_Tao: "Sáng tạo",
		Giao_Tiep: "Giao tiếp",
		Giang_Day: "Giảng dạy",
		Kinh_Doanh: "Kinh doanh",
		Con_So_Du_Lieu: "Con số, dữ liệu",
		Cham_Soc_Suc_Khoe: "Chăm sóc sức khỏe",
		Tranh_Bien_Luat: "Tranh biện, luật"
	};
	const abilityNames = {
		Tu_Duy_Logic: "Tư duy logic",
		Thao_Tac_Ky_Thuat: "Thao tác kỹ thuật",
		Tham_My_Nghe_Thuat: "Thẩm mỹ – nghệ thuật",
		Ngon_Ngu_Dien_Dat: "Ngôn ngữ, diễn đạt",
		To_Chuc_Lanh_Dao: "Tổ chức, lãnh đạo",
		Phan_Tich_Chi_Tiet: "Phân tích chi tiết"
	};
	let knowledgeBase = null;

	function keyOf(attr, value) {
		return attr + "\u0000" + value;
	}

	function combineCf(left, right) {
		if (left > 0 && right > 0) return left + right * (1 - left);
		if (left < 0 && right < 0) return left + right * (1 + left);
		return (left + right) / (1 - Math.min(Math.abs(left), Math.abs(right)));
	}

	function addFact(memory, attr, value, cf, timestamp, initial) {
		const key = keyOf(attr, value);
		if (!memory.has(key)) {
			memory.set(key, {
				attr: attr,
				value: value,
				cf: 0,
				timetag: timestamp,
				version: 0,
				contributions: {},
				initial: Boolean(initial)
			});
		}
		const fact = memory.get(key);
		if (initial) {
			fact.cf = cf;
			fact.initial = true;
		}
		return fact;
	}

	function factValues(memory, attr) {
		return Array.from(memory.values())
			.filter(function (fact) {
				return fact.attr === attr && fact.cf > knowledgeBase.constants.CF_THRESHOLD;
			})
			.map(function (fact) { return fact.value; })
			.sort();
	}

	function evaluateCondition(condition, state) {
		const operation = condition[0];
		const attr = condition[1];
		const value = condition[2];

		if (["ge", "gt", "lt", "le"].includes(operation)) {
			const numericValue = state.numeric[attr];
			if (numericValue === undefined || numericValue === null) return null;
			const satisfied = {
				ge: numericValue >= value,
				gt: numericValue > value,
				lt: numericValue < value,
				le: numericValue <= value
			}[operation];
			return satisfied ? { cf: 1, premises: [] } : null;
		}

		if (operation === "eq" || operation === "has") {
			const fact = state.memory.get(keyOf(attr, value));
			if (!fact || fact.cf <= knowledgeBase.constants.CF_THRESHOLD) return null;
			return { cf: fact.cf, premises: [{ attr: attr, value: value, version: fact.version }] };
		}

		if (operation === "exists") {
			const matching = Array.from(state.memory.values()).filter(function (fact) {
				return fact.attr === attr && fact.cf > knowledgeBase.constants.CF_THRESHOLD;
			});
			if (!matching.length) return null;
			return {
				cf: Math.max.apply(null, matching.map(function (fact) { return fact.cf; })),
				premises: matching.map(function (fact) {
					return { attr: fact.attr, value: fact.value, version: fact.version };
				})
			};
		}

		if (operation === "empty") {
			return Array.from(state.memory.values()).some(function (fact) {
				return fact.attr === attr && fact.cf > knowledgeBase.constants.CF_THRESHOLD;
			}) ? null : { cf: 1, premises: [] };
		}

		if (operation === "any" || operation === "all") {
			const results = condition[1].map(function (nested) {
				return evaluateCondition(nested, state);
			});
			if (operation === "any") {
				const satisfied = results.filter(Boolean);
				if (!satisfied.length) return null;
				return {
					cf: Math.max.apply(null, satisfied.map(function (result) { return result.cf; })),
					premises: satisfied.flatMap(function (result) { return result.premises; })
				};
			}
			if (results.some(function (result) { return result === null; })) return null;
			return {
				cf: Math.min.apply(null, results.map(function (result) { return result.cf; })),
				premises: results.flatMap(function (result) { return result.premises; })
			};
		}

		if (operation === "not") {
			return evaluateCondition(condition[1], state) === null ? { cf: 1, premises: [] } : null;
		}

		throw new Error("Toán tử luật không được hỗ trợ: " + operation);
	}

	function matchRule(rule, state) {
		const matches = rule.conds.map(function (condition) {
			return evaluateCondition(condition, state);
		});
		if (matches.some(function (match) { return match === null; })) return null;
		const premises = Array.from(new Map(matches.flatMap(function (match) {
			return match.premises;
		}).map(function (premise) {
			return [keyOf(premise.attr, premise.value) + ":" + premise.version, premise];
		})).values()).sort(function (left, right) {
			return keyOf(left.attr, left.value).localeCompare(keyOf(right.attr, right.value));
		});
		return {
			pcf: matches.length ? Math.min.apply(null, matches.map(function (match) { return match.cf; })) : 1,
			premises: premises
		};
	}

	function ruleRecency(rule, premises, state) {
		return Math.max.apply(null, premises.map(function (premise) {
			const fact = state.memory.get(keyOf(premise.attr, premise.value));
			return fact ? fact.timetag : 0;
		}).concat([0]));
	}

	function combineContributions(fact) {
		const values = Object.values(fact.contributions).sort(function (left, right) {
			return right - left;
		});
		return values.reduce(function (combined, value) {
			return combined === null ? value : combineCf(combined, value);
		}, null) || 0;
	}

	function explainFact(state, attr, value, path, depth) {
		const fact = state.memory.get(keyOf(attr, value));
		const prefix = "  ".repeat(depth);
		if (!fact) return [prefix + "• " + attr + " = " + value + " (chưa có dữ kiện)."];
		if (fact.initial) {
			return [prefix + "• " + attr + " = " + value + " — dữ liệu học sinh đã cung cấp."];
		}
		if (path.has(keyOf(attr, value))) {
			return [prefix + "• " + attr + " = " + value + " — đã dừng nhánh lặp."];
		}

		const nextPath = new Set(path);
		nextPath.add(keyOf(attr, value));
		const producingRules = Object.keys(fact.contributions).sort(function (left, right) {
			return (state.lastCycle[left] || 0) - (state.lastCycle[right] || 0);
		});
		let lines = [
			prefix + "• " + attr + " = " + value + " (CF " + fact.cf.toFixed(2) + ") được suy ra từ:"
		];

		producingRules.forEach(function (ruleId) {
			const rule = state.rulesById[ruleId];
			if (!rule) return;
			lines.push(prefix + "  ↳ " + ruleId + " (CF luật " + rule.cf.toFixed(2) + "): " + explainRule(rule, state));
			(state.lastPremises[ruleId] || []).forEach(function (premise) {
				lines = lines.concat(explainFact(state, premise.attr, premise.value, nextPath, depth + 2));
			});
		});
		return lines;
	}

	function runInference(student) {
		const memory = new Map();
		const numeric = {};
		const inputFacts = [];

		Object.entries(student.scores).forEach(function (entry) {
			if (entry[1] !== null && entry[1] !== undefined) numeric[entry[0]] = entry[1];
		});
		if (student.combination) {
			const combination = knowledgeBase.combinations[student.combination];
			if (combination && combination.every(function (subject) { return numeric[subject] !== undefined; })) {
				numeric.Tong_Diem_Du_Kien = Number(combination.reduce(function (total, subject) {
					return total + numeric[subject];
				}, 0).toFixed(2));
			}
		}

		student.interests.forEach(function (interest) {
			addFact(memory, "So_Thich", interest, 1, 0, true);
			inputFacts.push({ attr: "So_Thich", value: interest });
		});
		if (student.ability) {
			addFact(memory, "Nang_Luc_Noi_Troi", student.ability, 1, 0, true);
			inputFacts.push({ attr: "Nang_Luc_Noi_Troi", value: student.ability });
		}

		const state = {
			memory: memory,
			numeric: numeric,
			trace: [],
			fired: new Set(),
			lastPremises: {},
			lastCycle: {},
			rulesById: Object.fromEntries(knowledgeBase.rules.map(function (rule) { return [rule.id, rule]; }))
		};
		const maxCycles = 500;

		for (let cycle = 1; cycle <= maxCycles; cycle += 1) {
			let agenda = [];
			knowledgeBase.rules.forEach(function (rule) {
				const match = matchRule(rule, state);
				if (!match) return;
				const firingKey = rule.id + "|" + JSON.stringify(match.premises);
				if (state.fired.has(firingKey)) return;
				agenda.push({
					rule: rule,
					match: match,
					firingKey: firingKey,
					recency: ruleRecency(rule, match.premises, state)
				});
			});

			const primaryAgenda = agenda.filter(function (entry) { return entry.rule.tier <= 3; });
			if (primaryAgenda.length) agenda = primaryAgenda;
			if (!agenda.length) break;

			agenda.sort(function (left, right) {
				return right.rule.priority - left.rule.priority
					|| right.rule.specificity - left.rule.specificity
					|| right.recency - left.recency
					|| Number(left.rule.id.slice(1)) - Number(right.rule.id.slice(1));
			});

			const selected = agenda[0];
			const rule = selected.rule;
			state.fired.add(selected.firingKey);
			const attr = rule.then[0];
			const value = rule.then[1];
			const key = keyOf(attr, value);
			const wasNew = !memory.has(key);
			const fact = addFact(memory, attr, value, 0, cycle, false);
			const contribution = Number((rule.cf * selected.match.pcf).toFixed(6));
			fact.contributions[rule.id] = contribution;
			const previousCf = fact.cf;
			fact.cf = Number(combineContributions(fact).toFixed(6));
			if (wasNew || Math.abs(fact.cf - previousCf) > 1e-9) {
				fact.version += 1;
				fact.timetag = cycle;
			}

			state.lastPremises[rule.id] = selected.match.premises;
			state.lastCycle[rule.id] = cycle;
			state.trace.push({
				cycle: cycle,
				agenda: agenda.map(function (entry) {
					return { id: entry.rule.id, priority: entry.rule.priority };
				}),
				rule: rule,
				premises: selected.match.premises,
				premiseCf: selected.match.pcf,
				fact: { attr: attr, value: value },
				contribution: contribution,
				combinedCf: fact.cf,
				wasNew: wasNew
			});
			if (cycle === maxCycles) {
				throw new Error("Hệ suy diễn vượt quá " + maxCycles + " chu kỳ; đã dừng để tránh lặp vô hạn.");
			}
		}

		state.inputFacts = inputFacts;
		state.numeric = numeric;
		state.student = student;
		state.recommendations = Array.from(memory.values())
			.filter(function (fact) { return fact.attr === "Khuyen_Nghi_Chinh_Thuc"; })
			.sort(function (left, right) { return right.cf - left.cf; });
		return state;
	}

	function explainRule(rule, state) {
		const context = {
			Tong: state.numeric.Tong_Diem_Du_Kien === undefined ? "?" : state.numeric.Tong_Diem_Du_Kien.toFixed(1).replace(".", ","),
			To_Hop: state.student.combination || "?",
			So_Thich: state.student.interests.map(function (value) { return interestNames[value]; }).join(", ") || "?",
			Holland: factValues(state.memory, "Ma_Holland").join(", ") || "?"
		};
		Object.keys(scoreNames).forEach(function (attr) {
			context[attr] = state.numeric[attr] === undefined ? "?" : state.numeric[attr].toFixed(1).replace(".", ",");
		});
		return rule.template.replace(/\{([^}]+)\}/g, function (match, key) {
			return Object.prototype.hasOwnProperty.call(context, key) ? context[key] : match;
		});
	}

	function factDisplay(attr, value) {
		if (attr === "The_Manh_Khoi") return "Tổ hợp thế mạnh " + value.replace("KHOI_", "");
		if (attr === "Ma_Holland") {
			const names = { R_REALISTIC: "Thực tế (R)", I_INVESTIGATIVE: "Nghiên cứu (I)", A_ARTISTIC: "Nghệ thuật (A)", S_SOCIAL: "Xã hội (S)", E_ENTERPRISING: "Quản lý/kinh doanh (E)", C_CONVENTIONAL: "Nghiệp vụ (C)" };
			return names[value] || value;
		}
		if (attr === "Phan_Khuc_Diem") {
			return {
				TOP_DAU: "Phân khúc điểm mô phỏng: Top đầu",
				KHA_TOT: "Phân khúc điểm mô phỏng: Khá – tốt",
				AN_TOAN: "Phân khúc điểm mô phỏng: An toàn"
			}[value] || value;
		}
		if (attr === "Nhom_Nganh_Phu_Hop") return knowledgeBase.nhom_nganh[value] || value;
		return value;
	}

	function recommendationDescription(recKey, state) {
		const rec = knowledgeBase.recommendations[recKey];
		if (rec.mo_ta === "dynamic:nhom") {
			const groups = factValues(state.memory, "Nhom_Nganh_Phu_Hop").map(function (group) {
				return knowledgeBase.nhom_nganh[group];
			});
			return "Hướng nhóm ngành tham khảo: " + groups.join(", ") + " (chưa đủ dữ liệu để chốt ngành cụ thể).";
		}
		if (rec.mo_ta === "dynamic:holland") {
			const groups = [];
			factValues(state.memory, "Ma_Holland").forEach(function (holland) {
				(knowledgeBase.holland_hints[holland] || []).forEach(function (group) {
					if (!groups.includes(knowledgeBase.nhom_nganh[group])) groups.push(knowledgeBase.nhom_nganh[group]);
				});
			});
			const safety = factValues(state.memory, "Phan_Khuc_Diem").includes("AN_TOAN")
				? " Mức điểm mô phỏng ở phân khúc an toàn; hãy tìm hiểu thêm các chương trình phù hợp và phương thức xét tuyển."
				: "";
			return "Gợi ý tham khảo theo Holland (" + factValues(state.memory, "Ma_Holland").join(", ") + "): " + groups.join(", ") + "." + safety;
		}
		if (rec.mo_ta === "dynamic:insufficient") {
			return "Chưa đủ căn cứ để khuyến nghị. Cần bổ sung điểm môn học, sở thích hoặc năng lực nổi trội.";
		}

		const majors = rec.nganh.map(function (majorId) {
			const major = knowledgeBase.major_catalog[majorId];
			if (!major) return majorId;
			let codes = major.ma_hien_hanh ? "mã hiện hành " + major.ma_hien_hanh : "";
			if (major.ma_moi && major.xac_minh_tt74) codes += (codes ? " · " : "") + "mã mới " + major.ma_moi;
			else if (major.ma_moi) codes += (codes ? " · " : "") + "mã mới tham khảo " + major.ma_moi;
			return major.ten + (codes ? " (" + codes + ")" : "");
		});
		const group = knowledgeBase.nhom_nganh[rec.ma_nhom] || "Nhóm ngành tham khảo";
		let description = group + " — " + majors.join("; ") + " — " + rec.nhom_truong + ".";
		if (rec.mo_ta) description += " Lưu ý: " + rec.mo_ta;
		return description;
	}

	function appendText(parent, tagName, className, text) {
		const element = document.createElement(tagName);
		if (className) element.className = className;
		element.textContent = text;
		parent.appendChild(element);
		return element;
	}

	function renderFacts(memory, attrs, parent) {
		const facts = Array.from(memory.values()).filter(function (fact) {
			return attrs.includes(fact.attr) && !fact.initial && fact.cf > knowledgeBase.constants.CF_THRESHOLD;
		});
		facts.sort(function (left, right) {
			return left.attr.localeCompare(right.attr) || right.cf - left.cf;
		});
		facts.forEach(function (fact) {
			const item = appendText(parent, "span", "result-chip", factDisplay(fact.attr, fact.value));
			appendText(item, "small", "chip-cf", "CF " + fact.cf.toFixed(2));
		});
	}

	function renderRecommendations(state) {
		recommendationList.replaceChildren();
		derivedFacts.replaceChildren();
		explanationList.replaceChildren();
		traceList.replaceChildren();
		intermediateResults.replaceChildren();

		const recommendations = state.recommendations;
		const heading = document.getElementById("result-heading");
		const summary = document.getElementById("result-summary");
		const name = state.student.name;
		heading.textContent = name ? "Gợi ý hướng đi dành cho " + name + "." : "Các hướng ngành nghề phù hợp để bạn tham khảo.";
		summary.replaceChildren();
		appendText(summary, "span", "", recommendations.length
			? "Khuyến nghị được suy ra từ hồ sơ và các luật đã kích hoạt."
			: "Hệ thống chưa tìm thấy luật khuyến nghị ngành phù hợp với hồ sơ hiện tại.");
		const profileDetails = [];
		if (state.student.combination) {
			profileDetails.push("Tổ hợp " + state.student.combination
				+ (state.numeric.Tong_Diem_Du_Kien === undefined ? "" : " · Tổng " + state.numeric.Tong_Diem_Du_Kien.toFixed(1)));
		}
		if (state.student.interests.length) {
			profileDetails.push("Sở thích: " + state.student.interests.map(function (value) { return interestNames[value]; }).join(", "));
		}
		if (state.student.ability) profileDetails.push("Năng lực: " + abilityNames[state.student.ability]);
		if (profileDetails.length) appendText(summary, "span", "profile-summary", profileDetails.join(" · "));
		appendText(summary, "span", "profile-summary", "Loại điểm: " + ({
			hoc_ba: "học bạ",
			thi_thu: "thi thử",
			thi_chinh_thuc: "thi chính thức"
		}[state.student.scoreType] || "tham khảo"));

		noResults.hidden = recommendations.length > 0;
		recommendationList.hidden = recommendations.length === 0;
		intermediateResults.hidden = recommendations.length > 0;

		const derivedPanel = document.createElement("div");
		derivedPanel.className = "derived-facts";
		appendText(derivedPanel, "h3", "", "Hồ sơ suy luận trung gian");
		renderFacts(state.memory, ["The_Manh_Khoi", "Ma_Holland", "Phan_Khuc_Diem", "Nhom_Nganh_Phu_Hop"], derivedPanel);
		derivedFacts.appendChild(derivedPanel);

		recommendations.forEach(function (fact, index) {
			const recKey = fact.value;
			const rec = knowledgeBase.recommendations[recKey];
			const card = document.createElement("article");
			card.className = "recommendation-card";
			const topLine = appendText(card, "div", "recommendation-topline", "");
			appendText(topLine, "span", "recommendation-code", "GỢI Ý " + String(index + 1).padStart(2, "0"));
			appendText(topLine, "span", "recommendation-step", "CF " + fact.cf.toFixed(2));
			const group = rec.ma_nhom ? knowledgeBase.nhom_nganh[rec.ma_nhom] : "Định hướng tham khảo";
			appendText(card, "h3", "", group);
			appendText(card, "p", "", recommendationDescription(recKey, state));
			const ruleIds = state.why("Khuyen_Nghi_Chinh_Thuc", recKey);
			if (ruleIds.length) {
				const badgeLine = appendText(card, "div", "recommendation-rule", "Luật kích hoạt: ");
				ruleIds.forEach(function (ruleId, ruleIndex) {
					if (ruleIndex) badgeLine.appendChild(document.createTextNode(" "));
					appendText(badgeLine, "span", "rule-badge", ruleId);
				});
			}
			recommendationList.appendChild(card);

			const explanation = document.createElement("article");
			explanation.className = "explanation-item";
			appendText(explanation, "h4", "", "Vì sao hệ thống gợi ý " + group + "? (CF " + fact.cf.toFixed(2) + ")");
			const ruleIdsInOrder = state.why("Khuyen_Nghi_Chinh_Thuc", recKey);
			ruleIdsInOrder.forEach(function (ruleId) {
				const rule = state.rulesById[ruleId];
				if (!rule) return;
				const detail = document.createElement("div");
				detail.className = "proof-rule";
				appendText(detail, "strong", "proof-rule-id", ruleId + " · tầng " + rule.tier + " · Priority " + rule.priority + " · CF " + rule.cf.toFixed(2));
				appendText(detail, "p", "", explainRule(rule, state));
				(rule.conds || []).forEach(function (condition) {
					if (["ge", "gt", "lt", "le"].includes(condition[0])) {
						const actual = state.numeric[condition[1]];
						appendText(detail, "small", "proof-premise", scoreNames[condition[1]] + ": " + (actual === undefined ? "chưa cung cấp" : actual.toFixed(1)) + " (điều kiện " + condition[0] + " " + condition[2] + ")");
					} else if (condition[0] === "has" || condition[0] === "eq") {
						appendText(detail, "small", "proof-premise", factDisplay(condition[1], condition[2]));
					}
				});
				explanation.appendChild(detail);
			});
			explanationList.appendChild(explanation);
		});

		if (!recommendations.length) {
			appendText(explanationList, "p", "field-note", state.trace.length
				? "Hệ thống đã suy ra các dữ kiện trung gian ở trên nhưng chưa có kết luận ngành cụ thể."
				: "Chưa có luật nào được kích hoạt. Hãy bổ sung thêm thông tin học tập, sở thích hoặc năng lực.");
		}

		state.trace.forEach(function (step) {
			const row = document.createElement("article");
			row.className = "trace-step";
			appendText(row, "span", "trace-step-number", "CHU KỲ " + step.cycle);
			const content = document.createElement("div");
			content.className = "trace-step-content";
			step.agenda.forEach(function (entry) {
				appendText(content, "span", "rule-badge", entry.id + " · P" + entry.priority);
			});
			appendText(content, "p", "", "Chọn " + step.rule.id + " → " + factDisplay(step.fact.attr, step.fact.value) + ".");
			appendText(content, "p", "", "Độ tin cậy: CF tiền đề " + step.premiseCf.toFixed(2)
				+ " × CF luật " + step.rule.cf.toFixed(2) + " = " + step.contribution.toFixed(2)
				+ " · CF sau hợp nhất " + step.combinedCf.toFixed(2) + ".");
			appendText(content, "p", "", explainRule(step.rule, state));
			row.appendChild(content);
			traceList.appendChild(row);
		});

		const inputs = [];
		state.inputFacts.forEach(function (fact) {
			inputs.push(fact.attr === "So_Thich" ? interestNames[fact.value] : abilityNames[fact.value]);
		});
		Object.entries(state.student.scores).forEach(function (entry) {
			if (entry[1] !== null) inputs.push(scoreNames[entry[0]] + " " + entry[1].toFixed(1));
		});
		if (state.student.combination) inputs.push("Tổ hợp " + state.student.combination);
		if (inputs.length) appendText(derivedPanel, "p", "derived-inputs", "Thông tin đã nhập: " + inputs.join(" · "));
	}

	function getStudentProfile() {
		const scores = {};
		Object.keys(scoreNames).forEach(function (fieldName) {
			const input = document.getElementById(fieldName);
			scores[fieldName] = input.value === "" ? null : Number(input.value);
		});
		return {
			name: document.getElementById("student-name").value.trim(),
			scores: scores,
			scoreType: document.getElementById("score-type").value,
			combination: document.getElementById("To_Hop_Du_Kien").value,
			ability: document.getElementById("Nang_Luc_Noi_Troi").value,
			interests: Array.from(form.querySelectorAll('input[name="So_Thich"]:checked')).map(function (input) {
				return input.value;
			})
		};
	}

	function updateSelectedCount() {
		const profile = getStudentProfile();
		const countSelected = Object.values(profile.scores).filter(function (value) { return value !== null; }).length
			+ profile.interests.length
			+ (profile.ability ? 1 : 0)
			+ (profile.combination ? 1 : 0);
		count.textContent = String(countSelected);
	}

	function why(attr, value, state, visited, orderedRules) {
		const fact = state.memory.get(keyOf(attr, value));
		if (!fact) return;
		Object.keys(fact.contributions).forEach(function (ruleId) {
			if (visited.has(ruleId)) return;
			visited.add(ruleId);
			(state.lastPremises[ruleId] || []).forEach(function (premise) {
				const premiseFact = state.memory.get(keyOf(premise.attr, premise.value));
				if (premiseFact && !premiseFact.initial) why(premise.attr, premise.value, state, visited, orderedRules);
			});
			orderedRules.push(ruleId);
		});
	}

	form.addEventListener("input", updateSelectedCount);
	form.addEventListener("change", updateSelectedCount);

	form.addEventListener("submit", function (event) {
		event.preventDefault();
		if (!knowledgeBase) {
			error.hidden = false;
			error.textContent = "Cơ sở tri thức chưa sẵn sàng. Hãy tải lại trang hoặc kiểm tra kết nối tới máy chủ.";
			return;
		}

		const student = getStudentProfile();
		const providedScores = Object.values(student.scores).some(function (value) { return value !== null; });
		if (!providedScores && !student.interests.length && !student.ability) {
			error.hidden = false;
			error.textContent = "Nhập ít nhất một điểm môn học hoặc chọn sở thích/năng lực để hệ thống có căn cứ tư vấn.";
			return;
		}

		const invalidScore = Object.entries(student.scores).find(function (entry) {
			return entry[1] !== null && (!Number.isFinite(entry[1]) || entry[1] < 0 || entry[1] > 10);
		});
		if (invalidScore) {
			const input = document.getElementById(invalidScore[0]);
			input.setCustomValidity("Điểm phải nằm trong khoảng 0 đến 10.");
			input.reportValidity();
			input.focus();
			input.setCustomValidity("");
			return;
		}

		error.hidden = true;
		try {
			const state = runInference(student);
			state.why = function (attr, value) {
				const orderedRules = [];
				why(attr, value, state, new Set(), orderedRules);
				return orderedRules.sort(function (left, right) {
					return (state.lastCycle[left] || 0) - (state.lastCycle[right] || 0);
				});
			};
			renderRecommendations(state);
			resultSection.hidden = false;
			resultSection.scrollIntoView({ behavior: "smooth", block: "start" });
		} catch (inferenceError) {
			error.hidden = false;
			error.textContent = "Không thể hoàn tất suy diễn: " + inferenceError.message;
		}
	});

	document.getElementById("edit-profile").addEventListener("click", function () {
		document.getElementById("one").scrollIntoView({ behavior: "smooth", block: "start" });
	});

	document.getElementById("new-profile").addEventListener("click", function () {
		form.reset();
		updateSelectedCount();
		error.hidden = true;
		resultSection.hidden = true;
		document.getElementById("one").scrollIntoView({ behavior: "smooth", block: "start" });
	});

	fetch("../kb/rules_kb.json")
		.then(function (response) {
			if (!response.ok) throw new Error("Không tải được kb/rules_kb.json (HTTP " + response.status + ").");
			return response.json();
		})
		.then(function (data) {
			if (!Array.isArray(data.rules) || !data.recommendations || !data.major_catalog) {
				throw new Error("Định dạng cơ sở tri thức không hợp lệ.");
			}
			knowledgeBase = data;
			knowledgeStatus.textContent = "Đã nạp " + data.rules.length + " luật · " + Object.keys(data.nhom_nganh).length + " nhóm ngành · " + Object.keys(data.major_catalog).length + " ngành trong danh mục.";
			knowledgeStatus.classList.add("is-ready");
			document.getElementById("recommend-button").disabled = false;
		})
		.catch(function (loadError) {
			knowledgeStatus.textContent = "Không tải được cơ sở tri thức: " + loadError.message + " Hãy chạy web từ thư mục gốc dự án theo hướng dẫn.";
			knowledgeStatus.classList.add("is-error");
			document.getElementById("recommend-button").disabled = true;
		});
}());
