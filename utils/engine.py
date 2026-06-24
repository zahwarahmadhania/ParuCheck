from models import db, Rule, Disease, Symptom

def run_forward_chaining(selected_symptom_ids):
    """
    Runs Forward Chaining reasoning on the user's symptoms.
    
    Args:
        selected_symptom_ids (list): List of integers representing Symptom IDs.
        
    Returns:
        dict: A dictionary containing:
            - 'success': bool
            - 'primary_diagnosis': Disease model instance or None
            - 'confidence': float
            - 'triggered_rules': list of dicts with rule details
            - 'differential_diagnoses': list of dicts with alternative possibilities
    """
    if not selected_symptom_ids:
        return {
            'success': False,
            'primary_diagnosis': None,
            'confidence': 0.0,
            'triggered_rules': [],
            'differential_diagnoses': []
        }
    
    # 1. Initialize Working Memory with user's selected symptoms (facts)
    working_memory = set(int(sid) for sid in selected_symptom_ids)
    
    # 2. Retrieve all rules and their symptom associations
    rules = Rule.query.all()
    
    # 3. Forward Chaining Cycle
    # In pure forward chaining, we loop until no new facts (diseases) can be inferred
    inferred_diseases = {} # maps disease_id -> rule_id that triggered it
    new_fact_added = True
    
    while new_fact_added:
        new_fact_added = False
        for rule in rules:
            if rule.disease_id in inferred_diseases:
                continue # Already inferred this disease
                
            rule_symptom_ids = {s.id for s in rule.symptoms}
            
            # Check if all rule symptoms are subsets of working memory
            if rule_symptom_ids.issubset(working_memory):
                # Infer the disease
                inferred_diseases[rule.disease_id] = rule.id
                # Add the disease ID as a fact to working memory
                working_memory.add(f"D_{rule.disease_id}")
                new_fact_added = True
    
    # 4. Compile Results
    results = []
    
    # Check which diseases were fully inferred
    for disease_id, rule_id in inferred_diseases.items():
        disease = Disease.query.get(disease_id)
        rule = Rule.query.get(rule_id)
        if disease and rule:
            # Since all symptoms matched, confidence is 100%
            results.append({
                'disease': disease,
                'confidence': 100.0,
                'rule_code': rule.code,
                'matched_symptoms_count': len(rule.symptoms),
                'total_rule_symptoms_count': len(rule.symptoms),
                'is_inferred': True
            })
            
    # 5. If no rules were fully inferred, or to provide differential diagnoses,
    # we compute partial matches for all rules in the database.
    all_partial_matches = []
    user_symptom_set = set(int(sid) for sid in selected_symptom_ids)
    
    for rule in rules:
        # Skip rules that were fully inferred (already in results)
        if rule.disease_id in inferred_diseases:
            continue
            
        rule_symptom_ids = {s.id for s in rule.symptoms}
        matched_symptom_ids = user_symptom_set.intersection(rule_symptom_ids)
        
        if len(matched_symptom_ids) > 0:
            confidence = (len(matched_symptom_ids) / len(rule_symptom_ids)) * 100.0
            disease = Disease.query.get(rule.disease_id)
            if disease:
                all_partial_matches.append({
                    'disease': disease,
                    'confidence': round(confidence, 1),
                    'rule_code': rule.code,
                    'matched_symptoms_count': len(matched_symptom_ids),
                    'total_rule_symptoms_count': len(rule_symptom_ids),
                    'is_inferred': False
                })
                
    # Sort partial matches by confidence percentage (highest first), then by count
    all_partial_matches.sort(key=lambda x: (x['confidence'], x['matched_symptoms_count']), reverse=True)
    
    # Combine results
    all_results = results + all_partial_matches
    
    if not all_results:
        return {
            'success': False,
            'primary_diagnosis': None,
            'confidence': 0.0,
            'triggered_rules': [],
            'differential_diagnoses': []
        }
        
    primary = all_results[0]
    differentials = all_results[1:4] # Top 3 alternative/differential diagnoses
    
    # Compile details of triggered or partially matched rules
    triggered_rules_details = []
    for res in all_results:
        triggered_rules_details.append({
            'disease_name': res['disease'].name,
            'rule_code': res['rule_code'],
            'confidence': res['confidence'],
            'matched': res['matched_symptoms_count'],
            'total': res['total_rule_symptoms_count'],
            'is_inferred': res['is_inferred']
        })
        
    return {
        'success': True,
        'primary_diagnosis': primary['disease'],
        'confidence': primary['confidence'],
        'triggered_rules': triggered_rules_details,
        'differential_diagnoses': differentials
    }
