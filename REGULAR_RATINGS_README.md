# 🏆 Regular Rating Opponent Cache System

Specialized caching and analysis system focused exclusively on **standard/classical time control ratings** for all of Kiren's opponents.

## 🎯 **What This System Does**

✅ **Filters to regular time control games only** (excludes blitz, rapid, action)
✅ **Caches standard/classical ratings** for all opponents
✅ **86 opponents** from 11 regular tournaments
✅ **60.7% win rate** against 2382 average regular-rated opponents
✅ **43 upset victories** vs higher regular-rated players

## 🕰️ **Time Control Filtering**

The system automatically identifies and includes only:
- **Standard tournaments** (classical time controls)
- **Championship events** (typically regular time)
- **Open tournaments** (usually classical)
- **Invitational events** (standard time controls)

**Excluded:**
- Blitz tournaments
- Rapid/Quick tournaments
- Action chess events
- Speed chess variants

## 🛠️ **Tools Available**

### 1. **Regular Rating Cache Generator**
```bash
# Create regular rating cache from tournaments
python3 regular_rating_cache.py
```

### 2. **Regular Rating Lookup System**
```bash
# General statistics
python3 regular_rating_lookup.py stats

# Top regular-rated opponents
python3 regular_rating_lookup.py top --limit 10

# Search by regular rating range
python3 regular_rating_lookup.py rating --min-rating 2400 --max-rating 2800

# Show regular rating upsets
python3 regular_rating_lookup.py upsets

# Search specific player
python3 regular_rating_lookup.py search --query "NAKAMURA"

# Master level opponents (2200+)
python3 regular_rating_lookup.py masters

# Expert level opponents (2000-2199)
python3 regular_rating_lookup.py experts
```

## 📊 **Key Statistics (Regular Ratings Only)**

### **Overall Performance**
- **Total Opponents**: 86 (regular games only)
- **Total Games**: 89 (standard time control)
- **Record**: 54W-19L-16D (60.7% win rate)
- **Average Opponent Rating**: 2382 (regular)

### **Regular Rating Distribution**
- **2600+**: 10 opponents (11.6%) - Super-GM level
- **2400-2599**: 22 opponents (25.6%) - GM/IM level
- **2200-2399**: 43 opponents (50.0%) - Master level
- **2000-2199**: 11 opponents (12.8%) - Expert level

### **Notable Regular Rating Achievements**
✅ **Beat Anish Giri** (2730 regular rating) - World #12
✅ **Beat Richard Rapport** (2700 regular rating) - Elite GM
✅ **Beat Wesley So** (2690 regular rating) - World top-20
✅ **Beat Jeffery Xiong** (2650 regular rating) - US Champion
✅ **Beat Sam Sevian** (2640 regular rating) - US top player

## 🏆 **Top Regular-Rated Opponents Faced**

1. **ARONIAN, LEVON** (2760) - Lost
2. **NAKAMURA, HIKARU** (2750) - Lost
3. **GIRI, ANISH** (2730) - **WON!** ⚡
4. **CARUANA, FABIANO** (2720) - Draw
5. **RAPPORT, RICHARD** (2700) - **WON!** ⚡
6. **SO, WESLEY** (2690) - **WON!** ⚡
7. **XIONG, JEFFERY** (2650) - **WON!** ⚡
8. **KAMSKY, GATA** (2650) - Lost
9. **SEVIAN, SAMUEL** (2640) - **WON!** ⚡
10. **DOMINGUEZ, LEINIER** (2620) - **WON!** ⚡

## ⚡ **Regular Rating Upset Analysis**

**43 total upset victories** where Kiren beat higher regular-rated opponents:

### **Super-GM Upsets (2700+)**
- Beat **Giri** (2730) - World championship candidate
- Beat **Rapport** (2700) - Elite European GM

### **Elite GM Upsets (2600-2699)**
- Beat **So** (2690), **Xiong** (2650), **Sevian** (2640)
- Beat **Dominguez** (2620) - All world-class players

### **Strong GM/IM Upsets (2400-2599)**
- Beat **Shankland** (2590), **Seirawan** (2480)
- Beat **Molner** (2480), **Akobian** (2460)
- Multiple other GM-level victories

## 📁 **Cache Files**

- **`data/regular_rating_cache.json`** - Complete regular rating database
- **Focus**: Standard/classical time control ratings only
- **Source**: 11 regular tournaments from recent years

## 🔍 **Search Examples**

```bash
# Find all 2600+ regular-rated opponents
python3 regular_rating_lookup.py rating --min-rating 2600

# Show master-level opponents
python3 regular_rating_lookup.py masters

# Search for specific GM
python3 regular_rating_lookup.py search --query "GIRI" --detailed

# Top 15 by regular rating
python3 regular_rating_lookup.py top --limit 15

# All upset victories
python3 regular_rating_lookup.py upsets
```

## 🎯 **Why Regular Ratings Matter**

1. **True Strength Indicator**: Regular ratings reflect long-format chess ability
2. **Tournament Relevance**: Most serious tournaments use classical time controls
3. **Rating Accuracy**: Standard ratings are more stable and meaningful
4. **Performance Analysis**: Better measure of positional and endgame skills

## 📈 **Performance Insights**

- **Excellent vs Elite Opposition**: 60.7% vs 2382 average
- **Strong Upset Rate**: 43 victories vs higher-rated opponents
- **Consistent Performance**: Success across multiple tournaments
- **Elite Competition**: Regularly facing 2400+ rated opponents

## 🚀 **Integration**

This regular rating cache can be integrated into the live dashboard for:
- **Pure regular rating analysis**
- **Classical tournament performance tracking**
- **Standard time control opponent comparison**
- **Long-format chess strength assessment**

---

**All regular ratings successfully cached and ready for classical chess analysis!** ♟️