# TODO List for Tomorrow: Data Collection Launch Day 🚀

## **Mission: Start Collecting 50 Visual SKETCHPAD Trajectories**

### **✅ PROVEN WORKING:**
- Camera drag → `lookAngle` MCP commands ✅
- Right click → `rightClick` MCP commands ✅  
- getBotStatus after every action ✅
- Real MCP command generation ✅
- No double execution ✅

---

## **🎯 HIGH PRIORITY (Must Complete):**

### **1. Text Field for Assistant "Thoughts" (Essential)**
**Why**: Training data needs realistic assistant reasoning, not generic responses
**Current Problem**: All assistant messages say "I'll perform spatial reasoning actions"
**Goal**: Enter realistic thoughts like "I need to look around to find the tallest tree, then move closer to mark it"

**Implementation:**
- [ ] Add text field to data collection UI (might already exist from earlier work)
- [ ] Wire it to recording system so F5 captures this as the assistant's reasoning
- [ ] Test that conversations show realistic assistant thought process

**Time Estimate**: 30-60 minutes

### **2. Screenshots Saved in Conversations (Essential)**
**Why**: Multimodal training requires visual context with text
**Current Problem**: Only text state captured, no images in training data
**Goal**: Screenshots included in OpenAI conversation format

**Implementation:**
- [ ] Verify screenshot capture working (getBotStatus might already include this)
- [ ] Ensure screenshots are properly base64 encoded in conversation JSON
- [ ] Test that saved conversations include both text + images

**Time Estimate**: 30-60 minutes

---

## **🚀 IMMEDIATE ACTION (Same Day):**

### **3. Start Collecting 50 Trajectories**
**Process:**
1. **F5** → Enter task description and assistant reasoning
2. **Play** → Perform spatial reasoning demonstration naturally
3. **F6** → Save complete trajectory with screenshots + MCP commands
4. **Repeat** 50 times with varied spatial tasks

**Target Tasks:**
- [ ] "Find and mark the tallest tree" 
- [ ] "Navigate to high ground and mark good vantage points"
- [ ] "Identify and mark all chests in view"
- [ ] "Find building materials and mark their locations"
- [ ] "Explore cave entrances and mark them for later"
- [ ] Continue with varied spatial reasoning tasks...

**Success Criteria:**
- [ ] 50 complete trajectory files in `collected_trajectories/`
- [ ] Each contains realistic assistant reasoning + visual context
- [ ] Each shows complete MCP command sequences + game state responses
- [ ] Data format compatible with OpenAI training pipeline

---

## **⚠️ SCOPE CREEP RESISTANCE:**

### **❌ DO NOT DO (Tempting but not essential):**
- Controller connection (keyboard/mouse works fine)
- UI improvements (current interface sufficient)
- Performance optimization (speed is adequate)
- Error handling improvements (system is stable enough)
- Better logging/debugging (can debug after collecting data)
- Code cleanup/refactoring (works as-is)

### **🎯 THE RULE:**
> **"Does this directly help collect the first 50 trajectories?"**
> **If NO → Don't do it today!**

---

## **📊 SUCCESS METRICS:**

**By End of Day:**
- [ ] Text field working for assistant thoughts
- [ ] Screenshots saving in conversations  
- [ ] First 5-10 trajectories collected successfully
- [ ] Data format validated for training pipeline
- [ ] Clear path to complete all 50 trajectories

**By End of Week:**
- [ ] All 50 trajectories collected
- [ ] Phase 1 of Visual SKETCHPAD research COMPLETE
- [ ] Ready for Phase 2 model training

---

## **🎉 THE BIG PICTURE:**

**TODAY**: Complete the essential features for quality data
**THIS WEEK**: Collect 50 Visual SKETCHPAD trajectories  
**THIS MONTH**: Train first models on 3D spatial reasoning data
**THIS YEAR**: Prove 3D→web transfer learning works

**You've solved the hardest technical challenges. Now it's time to collect the data that will prove your research hypothesis!**

🚀 **FOCUS: COLLECT DATA, CHANGE THE WORLD!** 🚀